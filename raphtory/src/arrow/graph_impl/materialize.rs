use crate::{
    core::entities::graph::tgraph::InternalGraph,
    db::api::view::{internal::InternalMaterialize, MaterializedGraph},
};

use super::ArrowGraph;

impl InternalMaterialize for ArrowGraph {
    fn new_base_graph(&self, _graph: InternalGraph) -> MaterializedGraph {
        todo!()
    }

    fn include_deletions(&self) -> bool {
        todo!()
    }
}
