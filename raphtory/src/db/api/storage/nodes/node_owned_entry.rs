#[cfg(feature = "arrow")]
use crate::arrow::storage_interface::node::ArrowOwnedNode;
#[cfg(feature = "arrow")]
use crate::db::api::storage::variants::storage_variants::StorageVariants;
use crate::{
    core::{
        entities::{edges::edge_ref::EdgeRef, nodes::node_store::NodeStore, LayerIds, VID},
        storage::ArcEntry,
        Direction,
    },
    db::api::{
        storage::{
            nodes::{
                node_ref::NodeStorageRef,
                node_storage_ops::{NodeStorageIntoOps, NodeStorageOps},
            },
            tprop_storage_ops::TPropOps,
        },
        view::internal::NodeAdditions,
    },
};

pub enum NodeOwnedEntry {
    Mem(ArcEntry<NodeStore>),
    #[cfg(feature = "arrow")]
    Arrow(ArrowOwnedNode),
}

impl NodeOwnedEntry {
    pub fn as_ref(&self) -> NodeStorageRef {
        match self {
            NodeOwnedEntry::Mem(entry) => NodeStorageRef::Mem(entry),
            #[cfg(feature = "arrow")]
            NodeOwnedEntry::Arrow(entry) => NodeStorageRef::Arrow(entry.as_ref()),
        }
    }
}

macro_rules! for_all {
    ($value:expr, $pattern:pat => $result:expr) => {
        match $value {
            NodeOwnedEntry::Mem($pattern) => $result,
            #[cfg(feature = "arrow")]
            NodeOwnedEntry::Arrow($pattern) => $result,
        }
    };
}

#[cfg(feature = "arrow")]
macro_rules! for_all_iter {
    ($value:expr, $pattern:pat => $result:expr) => {{
        match $value {
            NodeOwnedEntry::Mem($pattern) => StorageVariants::Mem($result),
            NodeOwnedEntry::Arrow($pattern) => StorageVariants::Arrow($result),
        }
    }};
}

#[cfg(not(feature = "arrow"))]
macro_rules! for_all_iter {
    ($value:expr, $pattern:pat => $result:expr) => {{
        match $value {
            NodeOwnedEntry::Mem($pattern) => $result,
        }
    }};
}

impl<'a> NodeStorageOps<'a> for &'a NodeOwnedEntry {
    fn degree(self, layers: &LayerIds, dir: Direction) -> usize {
        for_all!(self, node => node.degree(layers, dir))
    }

    fn additions(self) -> NodeAdditions<'a> {
        for_all!(self, node => node.additions())
    }

    fn tprop(self, prop_id: usize) -> impl TPropOps<'a> {
        for_all_iter!(self, node => node.tprop(prop_id))
    }

    fn edges_iter(
        self,
        layers: &'a LayerIds,
        dir: Direction,
    ) -> impl Iterator<Item = EdgeRef> + 'a {
        for_all_iter!(self, node => node.edges_iter(layers, dir))
    }

    fn node_type_id(self) -> usize {
        for_all!(self, node => node.node_type_id())
    }

    fn vid(self) -> VID {
        for_all!(self, node => node.vid())
    }

    fn name(self) -> Option<&'a str> {
        for_all!(self, node => node.name())
    }

    fn find_edge(self, dst: VID, layer_ids: &LayerIds) -> Option<EdgeRef> {
        for_all!(self, node => node.find_edge(dst, layer_ids))
    }
}

impl NodeStorageIntoOps for NodeOwnedEntry {
    fn into_edges_iter(self, layers: LayerIds, dir: Direction) -> impl Iterator<Item = EdgeRef> {
        for_all_iter!(self, node => node.into_edges_iter(layers, dir))
    }

    fn into_neighbours_iter(self, layers: LayerIds, dir: Direction) -> impl Iterator<Item = VID> {
        for_all_iter!(self, node => node.into_neighbours_iter(layers, dir))
    }
}