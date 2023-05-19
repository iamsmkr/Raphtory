use crate::core::time::error::ParseTimeError;
use crate::core::time::{Interval, IntoTime};

/// Trait defining time query operations
pub trait TimeOps {
    type WindowedViewType: TimeOps;

    /// Return the timestamp of the default start for perspectives of the view (if any).
    fn start(&self) -> Option<i64>;

    /// Return the timestamp of the default for perspectives of the view (if any).
    fn end(&self) -> Option<i64>;

    /// Return the size of the window covered by this view
    fn window_size(&self) -> Option<u64> {
        match (self.start(), self.end()) {
            (Some(start), Some(end)) => Some((end - start) as u64),
            _ => None,
        }
    }

    /// Create a view including all events between `t_start` (inclusive) and `t_end` (exclusive)
    fn window<T: IntoTime>(&self, t_start: T, t_end: T) -> Self::WindowedViewType;

    /// Create a view including all events until `end` (inclusive)
    fn at<T: IntoTime>(&self, end: T) -> Self::WindowedViewType {
        self.window(i64::MIN, end.into_time().saturating_add(1))
    }

    /// Creates a `WindowSet` with the given `step` size and optional `start` and `end` times,    
    /// using an expanding window.
    ///
    /// An expanding window is a window that grows by `step` size at each iteration.
    fn expanding<I>(&self, step: I) -> Result<WindowSet<Self>, ParseTimeError>
    where
        Self: Sized + Clone + 'static,
        I: TryInto<Interval, Error = ParseTimeError>,
    {
        let parent = self.clone();
        match (self.start(), self.end()) {
            (Some(start), Some(end)) => {
                let step: Interval = step.try_into()?;

                Ok(WindowSet::new(parent, start, end, step, None))
            }
            _ => Ok(WindowSet::empty(parent)),
        }
    }

    /// Creates a `WindowSet` with the given `window` size and optional `step`, `start` and `end` times,
    /// using a rolling window.
    ///
    /// A rolling window is a window that moves forward by `step` size at each iteration.
    fn rolling<I>(&self, window: I, step: Option<I>) -> Result<WindowSet<Self>, ParseTimeError>
    where
        Self: Sized + Clone + 'static,
        I: TryInto<Interval, Error = ParseTimeError>,
    {
        let parent = self.clone();
        match (self.start(), self.end()) {
            (Some(start), Some(end)) => {
                let window: Interval = window.try_into()?;
                let step: Interval = match step {
                    Some(step) => step.try_into()?,
                    None => window,
                };
                Ok(WindowSet::new(parent, start, end, step, Some(window)))
            }
            _ => Ok(WindowSet::empty(parent)),
        }
    }
}

#[derive(Clone)]
pub struct WindowSet<T: TimeOps + Clone> {
    view: T,
    cursor: i64,
    end: i64,
    step: Interval,
    window: Option<Interval>,
}

impl<T: TimeOps + Clone + 'static> WindowSet<T> {
    fn new(view: T, start: i64, end: i64, step: Interval, window: Option<Interval>) -> Self {
        // let cursor_start = if step.epoch_alignment {
        //     let step = step.to_millis().unwrap() as i64;
        //     let prev_perspective_exclusive_end = (timeline_start / step) * step; // timeline.start 5 step 3 -> 3, timeline.start 6 step 3 -> 6, timeline.start 7 step 3 -> 6
        //     let prev_perspective_inclusive_end = prev_perspective_exclusive_end - 1;
        //     prev_perspective_inclusive_end + step
        // } else {
        //     timeline_start + step - 1
        // };
        let cursor_start = start + step - 1;
        Self {
            view,
            cursor: cursor_start,
            end,
            step,
            window,
        }
    }

    fn empty(view: T) -> Self {
        // timeline_start is greater than end, so no windows to return, even with end inclusive
        WindowSet::new(view, 1, 0, Default::default(), None)
    }

    // TODO: make this optionally public only for the development feature flag
    pub fn temporal(&self) -> bool {
        self.step.epoch_alignment
            || match self.window {
                Some(window) => window.epoch_alignment,
                None => false,
            }
    }

    /// Returns the time index of this window set
    pub fn time_index(&self, center: bool) -> TimeIndex<T> {
        TimeIndex {
            windowset: self.clone(),
            center,
        }
    }
}

pub struct TimeIndex<T: TimeOps + Clone> {
    windowset: WindowSet<T>,
    center: bool,
}

impl<T: TimeOps + Clone> Iterator for TimeIndex<T> {
    type Item = i64;

    fn next(&mut self) -> Option<Self::Item> {
        self.windowset.next().map(|view| {
            if self.center {
                view.start().unwrap() + ((view.end().unwrap() - view.start().unwrap()) / 2)
            } else {
                view.end().unwrap() - 1
            }
        })
    }
}

impl<T: TimeOps + Clone> Iterator for WindowSet<T> {
    type Item = T::WindowedViewType;
    fn next(&mut self) -> Option<Self::Item> {
        if self.cursor < self.end {
            let window_end = self.cursor + 1;
            let window_start = self.window.map(|w| window_end - w).unwrap_or(i64::MIN);
            let window = self.view.window(window_start, window_end);
            self.cursor = self.cursor + self.step;
            Some(window)
        } else {
            None
        }
    }
}

#[cfg(test)]
mod time_tests {
    use crate::core::time::TryIntoTime;
    use crate::db::graph::Graph;
    use crate::db::view_api::internal::GraphViewInternalOps;
    use crate::db::view_api::time::WindowSet;
    use crate::db::view_api::{GraphViewOps, TimeOps};
    use itertools::Itertools;

    // start inclusive, end exclusive
    fn graph_with_timeline(start: i64, end: i64) -> Graph {
        let g = Graph::new(4);
        g.add_vertex(start, 0, &vec![]).unwrap();
        g.add_vertex(end - 1, 0, &vec![]).unwrap();
        assert_eq!(g.start().unwrap(), start);
        assert_eq!(g.end().unwrap(), end);
        g
    }

    fn assert_bounds<G>(windows: WindowSet<G>, expected: Vec<(i64, i64)>)
    where
        G: GraphViewOps + GraphViewInternalOps,
    {
        let window_bounds = windows
            .map(|w| (w.start().unwrap(), w.end().unwrap()))
            .collect_vec();
        assert_eq!(window_bounds, expected)
    }

    #[test]
    fn rolling() {
        let g = graph_with_timeline(1, 7);
        let windows = g.rolling(2, None).unwrap();
        let expected = vec![(1, 3), (3, 5), (5, 7)];
        assert_bounds(windows, expected);

        let g = graph_with_timeline(1, 6);
        let windows = g.rolling(3, Some(2)).unwrap();
        let expected = vec![(0, 3), (2, 5)];
        assert_bounds(windows, expected.clone());

        let g = graph_with_timeline(0, 9).window(1, 6);
        let windows = g.rolling(3, Some(2)).unwrap();
        assert_bounds(windows, expected);
    }

    #[test]
    fn expanding() {
        let min = i64::MIN;
        let g = graph_with_timeline(1, 7);
        let windows = g.expanding(2).unwrap();
        let expected = vec![(min, 3), (min, 5), (min, 7)];
        assert_bounds(windows, expected);

        let g = graph_with_timeline(1, 6);
        let windows = g.expanding(2).unwrap();
        let expected = vec![(min, 3), (min, 5)];
        assert_bounds(windows, expected.clone());

        let g = graph_with_timeline(0, 9).window(1, 6);
        let windows = g.expanding(2).unwrap();
        assert_bounds(windows, expected);
    }

    #[test]
    fn rolling_dates() {
        let start = "2020-06-06 00:00:00".try_into_time().unwrap();
        let end = "2020-06-07 23:59:59.999".try_into_time().unwrap();
        let g = graph_with_timeline(start, end);
        let windows = g.rolling("1 day", None).unwrap();
        let expected = vec![(
            "2020-06-06 00:00:00".try_into_time().unwrap(), // entire 2020-06-06
            "2020-06-07 00:00:00".try_into_time().unwrap(),
        )];
        assert_bounds(windows, expected);

        let start = "2020-06-06 00:00:00".try_into_time().unwrap();
        let end = "2020-06-08 00:00:00".try_into_time().unwrap();
        let g = graph_with_timeline(start, end);
        let windows = g.rolling("1 day", None).unwrap();
        let expected = vec![
            (
                "2020-06-06 00:00:00".try_into_time().unwrap(), // entire 2020-06-06
                "2020-06-07 00:00:00".try_into_time().unwrap(),
            ),
            (
                "2020-06-07 00:00:00".try_into_time().unwrap(), // entire 2020-06-07
                "2020-06-08 00:00:00".try_into_time().unwrap(),
            ),
        ];
        assert_bounds(windows, expected);

        // TODO: turn this back on if we bring bach epoch alignment for unwindowed graphs
        // let start = "2020-06-05 23:59:59.999".into_time().unwrap();
        // let end = "2020-06-07 00:00:00.000".into_time().unwrap();
        // let g = graph_with_timeline(start, end);
        // let windows = g.rolling("1 day", None).unwrap();
        // let expected = vec![
        //     (
        //         "2020-06-05 00:00:00".into_time().unwrap(), // entire 2020-06-06
        //         "2020-06-06 00:00:00".into_time().unwrap(),
        //     ),
        //     (
        //         "2020-06-06 00:00:00".into_time().unwrap(), // entire 2020-06-07
        //         "2020-06-07 00:00:00".into_time().unwrap(),
        //     ),
        // ];
        // assert_bounds(windows, expected);
    }

    #[test]
    fn expanding_dates() {
        let min = i64::MIN;

        let start = "2020-06-06 00:00:00".try_into_time().unwrap();
        let end = "2020-06-07 23:59:59.999".try_into_time().unwrap();
        let g = graph_with_timeline(start, end);
        let windows = g.expanding("1 day").unwrap();
        let expected = vec![(min, "2020-06-07 00:00:00".try_into_time().unwrap())];
        assert_bounds(windows, expected);

        let start = "2020-06-06 00:00:00".try_into_time().unwrap();
        let end = "2020-06-08 00:00:00".try_into_time().unwrap();
        let g = graph_with_timeline(start, end);
        let windows = g.expanding("1 day").unwrap();
        let expected = vec![
            (min, "2020-06-07 00:00:00".try_into_time().unwrap()),
            (min, "2020-06-08 00:00:00".try_into_time().unwrap()),
        ];
        assert_bounds(windows, expected);
    }
}
