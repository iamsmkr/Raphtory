//! Helper functions for the Python bindings.
//!
//! This module contains helper functions for the Python bindings.
//! These functions are not part of the public API and are not exported to the Python module.
use crate::{
    core::{
        entities::{nodes::node_ref::NodeRef, GidRef},
        storage::timeindex::AsTime,
        utils::time::{error::ParseTimeError, Interval, IntoTime, TryIntoTime},
        Prop, PropUnwrap,
    },
    db::api::view::*,
    python::graph::node::PyNode,
};
use chrono::{DateTime, FixedOffset, NaiveDateTime, Utc};
use numpy::IntoPyArray;
use pyo3::{
    exceptions::{PyRuntimeError, PyTypeError},
    prelude::*,
    types::PyDateTime,
};
use serde::Serialize;
use std::{future::Future, thread};

pub mod errors;
pub(crate) mod export;
mod module_helpers;

/// Extract a `NodeRef` from a Python object.
/// The object can be a `str`, `u64` or `PyNode`.
/// If the object is a `PyNode`, the `NodeRef` is extracted from the `PyNode`.
/// If the object is a `str`, the `NodeRef` is created from the `str`.
/// If the object is a `int`, the `NodeRef` is created from the `int`.
///
/// Arguments
///     vref: The Python object to extract the `NodeRef` from.
///
/// Returns
///    A `NodeRef` extracted from the Python object.
impl<'source> FromPyObject<'source> for NodeRef<'source> {
    fn extract(vref: &'source PyAny) -> PyResult<Self> {
        if let Ok(s) = vref.extract::<&'source str>() {
            Ok(NodeRef::External(GidRef::Str(s)))
        } else if let Ok(gid) = vref.extract::<u64>() {
            Ok(NodeRef::External(GidRef::U64(gid)))
        } else if let Ok(v) = vref.extract::<PyNode>() {
            Ok(NodeRef::Internal(v.node.node))
        } else {
            Err(PyTypeError::new_err("Not a valid node"))
        }
    }
}

fn parse_email_timestamp(timestamp: &str) -> PyResult<i64> {
    Python::with_gil(|py| {
        let email_utils = PyModule::import(py, "email.utils")?;
        let datetime = email_utils.call_method1("parsedate_to_datetime", (timestamp,))?;
        let py_seconds = datetime.call_method1("timestamp", ())?;
        let seconds = py_seconds.extract::<f64>()?;
        Ok(seconds as i64 * 1000)
    })
}

#[derive(Clone, Serialize)]
pub struct PyTime {
    parsing_result: i64,
}

impl<'source> FromPyObject<'source> for PyTime {
    fn extract(time: &'source PyAny) -> PyResult<Self> {
        if let Ok(string) = time.extract::<String>() {
            let timestamp = string.as_str();
            let parsing_result = timestamp
                .try_into_time()
                .or_else(|e| parse_email_timestamp(timestamp).map_err(|_| e))?;
            return Ok(PyTime::new(parsing_result));
        }
        if let Ok(number) = time.extract::<i64>() {
            return Ok(PyTime::new(number.into_time()));
        }
        if let Ok(float_time) = time.extract::<f64>() {
            // seconds since Unix epoch as returned by python `timestamp`
            let float_ms = float_time * 1000.0;
            let float_ms_trunc = float_ms.round();
            let rel_err = (float_ms - float_ms_trunc).abs() / (float_ms.abs() + f64::EPSILON);
            if rel_err > 4.0 * f64::EPSILON {
                return Err(PyRuntimeError::new_err(
                    "Float timestamps with more than millisecond precision are not supported.",
                ));
            }
            return Ok(PyTime::new(float_ms_trunc as i64));
        }
        if let Ok(parsed_datetime) = time.extract::<DateTime<FixedOffset>>() {
            return Ok(PyTime::new(parsed_datetime.into_time()));
        }
        if let Ok(parsed_datetime) = time.extract::<NaiveDateTime>() {
            // Important, this is needed to ensure that naive DateTime objects are treated as UTC and not local time
            return Ok(PyTime::new(parsed_datetime.into_time()));
        }
        if let Ok(py_datetime) = time.extract::<&PyDateTime>() {
            let time = (py_datetime.call_method0("timestamp")?.extract::<f64>()? * 1000.0) as i64;
            return Ok(PyTime::new(time));
        }
        let message = format!("time '{time}' must be a str, datetime, float, or an integer");
        Err(PyTypeError::new_err(message))
    }
}
impl PyTime {
    fn new(parsing_result: i64) -> Self {
        Self { parsing_result }
    }
    pub const MIN: PyTime = PyTime {
        parsing_result: i64::MIN,
    };
    pub const MAX: PyTime = PyTime {
        parsing_result: i64::MAX,
    };
}

impl IntoTime for PyTime {
    fn into_time(self) -> i64 {
        self.parsing_result
    }
}

pub(crate) struct PyInterval {
    interval: Result<Interval, ParseTimeError>,
}

impl PyInterval {
    fn new<I>(interval: I) -> Self
    where
        I: TryInto<Interval, Error = ParseTimeError>,
    {
        Self {
            interval: interval.try_into(),
        }
    }
}

impl<'source> FromPyObject<'source> for PyInterval {
    fn extract(interval: &'source PyAny) -> PyResult<Self> {
        let string = interval.extract::<String>();
        let result = string.map(|string| PyInterval::new(string.as_str()));

        let result = result.or_else(|_| {
            let number = interval.extract::<u64>();
            number.map(PyInterval::new)
        });

        result.map_err(|_| {
            let message = format!("interval '{interval}' must be a str or an unsigned integer");
            PyTypeError::new_err(message)
        })
    }
}

impl TryFrom<PyInterval> for Interval {
    type Error = ParseTimeError;
    fn try_from(value: PyInterval) -> Result<Self, Self::Error> {
        value.interval
    }
}

pub trait WindowSetOps {
    fn build_iter(&self) -> PyGenericIterator;
    fn time_index(&self, center: bool) -> PyGenericIterable;
}

impl<T> WindowSetOps for WindowSet<'static, T>
where
    T: TimeOps<'static> + Clone + Sync + Send + 'static,
    T::WindowedViewType: IntoPy<PyObject> + Send + 'static,
{
    fn build_iter(&self) -> PyGenericIterator {
        self.clone().into()
    }

    fn time_index(&self, center: bool) -> PyGenericIterable {
        let window_set = self.clone();

        if window_set.temporal() {
            let iterable = move || {
                let iter: Box<dyn Iterator<Item = DateTime<Utc>> + Send> = Box::new(
                    window_set
                        .clone()
                        .time_index(center)
                        .flat_map(|epoch| epoch.dt()),
                );
                iter
            };
            iterable.into()
        } else {
            (move || {
                let iter: Box<dyn Iterator<Item = i64> + Send> =
                    Box::new(window_set.time_index(center));
                iter
            })
            .into()
        }
    }
}

#[pyclass(name = "WindowSet")]
pub struct PyWindowSet {
    window_set: Box<dyn WindowSetOps + Send>,
}

impl<T> From<WindowSet<'static, T>> for PyWindowSet
where
    T: TimeOps<'static> + Clone + Sync + Send + 'static,
    T::WindowedViewType: IntoPy<PyObject> + Send + Sync,
{
    fn from(value: WindowSet<'static, T>) -> Self {
        Self {
            window_set: Box::new(value),
        }
    }
}

impl<T> IntoPy<PyObject> for WindowSet<'static, T>
where
    T: TimeOps<'static> + Clone + Sync + Send + 'static,
    T::WindowedViewType: IntoPy<PyObject> + Send + Sync,
{
    fn into_py(self, py: Python<'_>) -> PyObject {
        PyWindowSet::from(self).into_py(py)
    }
}

#[pymethods]
impl PyWindowSet {
    fn __iter__(&self) -> PyGenericIterator {
        self.window_set.build_iter()
    }

    /// Returns the time index of this window set
    ///
    /// It uses the last time of each window as the reference or the center of each if `center` is
    /// set to `True`
    ///
    /// Arguments:
    ///     center (bool): if True time indexes are centered. Defaults to False
    ///
    /// Returns:
    ///     Iterable: the time index"
    #[pyo3(signature = (center=false))]
    fn time_index(&self, center: bool) -> PyGenericIterable {
        self.window_set.time_index(center)
    }
}

#[pyclass(name = "Iterable")]
pub struct PyGenericIterable {
    build_iter: Box<dyn Fn() -> Box<dyn Iterator<Item = PyObject> + Send> + Send>,
}

impl<F, I, T> From<F> for PyGenericIterable
where
    F: (Fn() -> I) + Send + Sync + 'static,
    I: Iterator<Item = T> + Send + 'static,
    T: IntoPy<PyObject> + 'static,
{
    fn from(value: F) -> Self {
        let build_py_iter: Box<dyn Fn() -> Box<dyn Iterator<Item = PyObject> + Send> + Send> =
            Box::new(move || Box::new(value().map(|item| Python::with_gil(|py| item.into_py(py)))));
        Self {
            build_iter: build_py_iter,
        }
    }
}

#[pymethods]
impl PyGenericIterable {
    fn __iter__(&self) -> PyGenericIterator {
        (self.build_iter)().into()
    }
}

#[pyclass(name = "Iterator", unsendable)]
pub struct PyGenericIterator {
    iter: Box<dyn Iterator<Item = PyObject>>,
}

impl<I, T> From<I> for PyGenericIterator
where
    I: Iterator<Item = T> + 'static,
    T: IntoPy<PyObject> + 'static,
{
    fn from(value: I) -> Self {
        let py_iter = Box::new(value.map(|item| Python::with_gil(|py| item.into_py(py))));
        Self { iter: py_iter }
    }
}

impl IntoIterator for PyGenericIterator {
    type Item = PyObject;

    type IntoIter = Box<dyn Iterator<Item = PyObject>>;

    fn into_iter(self) -> Self::IntoIter {
        self.iter
    }
}

#[pymethods]
impl PyGenericIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }
    fn __next__(&mut self) -> Option<PyObject> {
        self.iter.next()
    }
}

#[pyclass(name = "NestedIterator")]
pub struct PyNestedGenericIterator {
    iter: BoxedIter<PyGenericIterator>,
}

impl<I, J, T> From<I> for PyNestedGenericIterator
where
    I: Iterator<Item = J> + Send + 'static,
    J: Iterator<Item = T> + Send + 'static,
    T: IntoPy<PyObject> + 'static,
{
    fn from(value: I) -> Self {
        let py_iter = Box::new(value.map(|item| item.into()));
        Self { iter: py_iter }
    }
}

#[pymethods]
impl PyNestedGenericIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }
    fn __next__(&mut self) -> Option<PyGenericIterator> {
        self.iter.next()
    }
}

pub enum NumpyArray {
    Bool(Vec<bool>),
    U32(Vec<u32>),
    U64(Vec<u64>),
    I32(Vec<i32>),
    I64(Vec<i64>),
    F32(Vec<f32>),
    F64(Vec<f64>),
    Props(Vec<Prop>),
}

impl FromIterator<Prop> for NumpyArray {
    fn from_iter<I: IntoIterator<Item = Prop>>(iter: I) -> Self {
        let mut iter = iter.into_iter().peekable();
        match iter.peek() {
            Some(Prop::Bool(_)) => Self::Bool(iter.filter_map(|p| p.into_bool()).collect()),
            Some(Prop::I32(_)) => Self::I32(iter.filter_map(|p| p.into_i32()).collect()),
            Some(Prop::I64(_)) => Self::I64(iter.filter_map(|p| p.into_i64()).collect()),
            Some(Prop::U32(_)) => Self::U32(iter.filter_map(|p| p.into_u32()).collect()),
            Some(Prop::U64(_)) => Self::U64(iter.filter_map(|p| p.into_u64()).collect()),
            Some(Prop::F32(_)) => Self::F32(iter.filter_map(|p| p.into_f32()).collect()),
            Some(Prop::F64(_)) => Self::F64(iter.filter_map(|p| p.into_f64()).collect()),
            _ => Self::Props(iter.collect()),
        }
    }
}

impl From<Vec<i64>> for NumpyArray {
    fn from(value: Vec<i64>) -> Self {
        NumpyArray::I64(value)
    }
}

impl IntoPy<PyObject> for NumpyArray {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            NumpyArray::Bool(value) => value.into_pyarray(py).to_object(py),
            NumpyArray::I32(value) => value.into_pyarray(py).to_object(py),
            NumpyArray::I64(value) => value.into_pyarray(py).to_object(py),
            NumpyArray::U32(value) => value.into_pyarray(py).to_object(py),
            NumpyArray::U64(value) => value.into_pyarray(py).to_object(py),
            NumpyArray::F32(value) => value.into_pyarray(py).to_object(py),
            NumpyArray::F64(value) => value.into_pyarray(py).to_object(py),
            NumpyArray::Props(vec) => match vec.first() {
                Some(Prop::Bool(_)) => {
                    Self::Bool(vec.into_iter().filter_map(|p| p.into_bool()).collect()).into_py(py)
                }
                Some(Prop::I32(_)) => {
                    Self::I32(vec.into_iter().filter_map(|p| p.into_i32()).collect()).into_py(py)
                }
                Some(Prop::I64(_)) => {
                    Self::I64(vec.into_iter().filter_map(|p| p.into_i64()).collect()).into_py(py)
                }
                Some(Prop::U32(_)) => {
                    Self::U32(vec.into_iter().filter_map(|p| p.into_u32()).collect()).into_py(py)
                }
                Some(Prop::U64(_)) => {
                    Self::U64(vec.into_iter().filter_map(|p| p.into_u64()).collect()).into_py(py)
                }
                Some(Prop::F32(_)) => {
                    Self::F32(vec.into_iter().filter_map(|p| p.into_f32()).collect()).into_py(py)
                }
                Some(Prop::F64(_)) => {
                    Self::F64(vec.into_iter().filter_map(|p| p.into_f64()).collect()).into_py(py)
                }
                _ => vec.into_py(py),
            },
        }
    }
}

// This function takes a function that returns a future instead of taking just a future because
// a task might return an unsendable future but what we can do is making a function returning that
// future which is sendable itself
pub fn execute_async_task<T, F, O>(task: T) -> O
where
    T: FnOnce() -> F + Send + 'static,
    F: Future<Output = O> + 'static,
    O: Send + 'static,
{
    Python::with_gil(|py| {
        py.allow_threads(move || {
            // we call `allow_threads` because the task might need to grab the GIL
            thread::spawn(move || {
                tokio::runtime::Builder::new_multi_thread()
                    .enable_all()
                    .build()
                    .unwrap()
                    .block_on(task())
            })
            .join()
            .expect("error when waiting for async task to complete")
        })
    })
}
