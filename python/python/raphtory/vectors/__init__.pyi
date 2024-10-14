###############################################################################
#                                                                             #
#                      AUTOGENERATED TYPE STUB FILE                           #
#                                                                             #
#    This file was automatically generated. Do not modify it directly.        #
#    Any changes made here may be lost when the file is regenerated.          #
#                                                                             #
###############################################################################

from typing import *
from raphtory import *
from raphtory.vectors import *
from raphtory.graphql import *
from raphtory.typing import *
from datetime import datetime
from pandas import DataFrame

class Document:
    def __init__(self, content, life=None):
        """Initialize self.  See help(type(self)) for accurate signature."""

    @property
    def content(self): ...
    @property
    def embedding(self): ...
    @property
    def entity(self): ...
    @property
    def life(self): ...

class VectorSelection:
    def __init__(self):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def add_edges(self, edges: list):
        """
        Add all the documents associated with the `edges` to the current selection

        Documents added by this call are assumed to have a score of 0.

        Args:
          edges (list):  a list of the edge ids or edges to add
        """

    def add_nodes(self, nodes: list):
        """
        Add all the documents associated with the `nodes` to the current selection

        Documents added by this call are assumed to have a score of 0.

        Args:
          nodes (list): a list of the node ids or nodes to add
        """

    def append(self, selection: Any):
        """
        Add all the documents in `selection` to the current selection

        Args:
          selection: a selection to be added

        Returns:
          The selection with the new documents
        """

    def edges(self):
        """Return the edges present in the current selection"""

    def expand(self, hops: int, window: Optional[Tuple[int | str, int | str]] = None):
        """
        Add all the documents `hops` hops away to the selection

        Two documents A and B are considered to be 1 hop away of each other if they are on the same
        entity or if they are on the same node/edge pair. Provided that, two nodes A and C are n
        hops away of  each other if there is a document B such that A is n - 1 hops away of B and B
        is 1 hop away of C.

        Args:
          hops (int): the number of hops to carry out the expansion
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered
        """

    def expand_documents_by_similarity(
        self,
        query: str | list,
        limit,
        window: Optional[Tuple[int | str, int | str]] = None,
    ):
        """
        Add the top `limit` adjacent documents with higher score for `query` to the selection

        The expansion algorithm is a loop with two steps on each iteration:
          1. All the documents 1 hop away of some of the documents included on the selection (and
        not already selected) are marked as candidates.
          2. Those candidates are added to the selection in descending order according to the
        similarity score obtained against the `query`.

        This loops goes on until the current selection reaches a total of `limit`  documents or
        until no more documents are available

        Args:
          query (str | list): the text or the embedding to score against
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered
        """

    def expand_edges_by_similarity(
        self,
        query: str | list,
        limit: int,
        window: Optional[Tuple[int | str, int | str]] = None,
    ):
        """
        Add the top `limit` adjacent edges with higher score for `query` to the selection

        This function has the same behavior as expand_entities_by_similarity but it only considers edges.

        Args:
          query (str | list): the text or the embedding to score against
          limit (int): the maximum number of new edges to add
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered
        """

    def expand_entities_by_similarity(
        self,
        query: str | list,
        limit,
        window: Optional[Tuple[int | str, int | str]] = None,
    ):
        """
        Add the top `limit` adjacent entities with higher score for `query` to the selection

        The expansion algorithm is a loop with two steps on each iteration:
          1. All the entities 1 hop away of some of the entities included on the selection (and
        not already selected) are marked as candidates.
          2. Those candidates are added to the selection in descending order according to the
        similarity score obtained against the `query`.

        This loops goes on until the number of new entities reaches a total of `limit`
        entities or until no more documents are available

        Args:
          query (str | list): the text or the embedding to score against
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered
        """

    def expand_nodes_by_similarity(
        self,
        query: str | list,
        limit: int,
        window: Optional[Tuple[int | str, int | str]] = None,
    ):
        """
        Add the top `limit` adjacent nodes with higher score for `query` to the selection

        This function has the same behavior as expand_entities_by_similarity but it only considers nodes.

        Args:
          query (str | list): the text or the embedding to score against
          limit (int): the maximum number of new nodes to add
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered
        """

    def get_documents(self):
        """Return the documents present in the current selection"""

    def get_documents_with_scores(self):
        """Return the documents alongside their scores present in the current selection"""

    def nodes(self):
        """Return the nodes present in the current selection"""

class VectorisedGraph:
    def __init__(self):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def documents_by_similarity(
        self,
        query: str | list,
        limit: int,
        window: Optional[Tuple[int | str, int | str]] = None,
    ) -> VectorSelection:
        """
        Search the top scoring documents according to `query` with no more than `limit` documents

        Args:
          query (str | list): the text or the embedding to score against
          limit (int): the maximum number of documents to search
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered

        Returns:
          VectorSelection: The vector selection resulting from the search
        """

    def edges_by_similarity(
        self,
        query: str | list,
        limit: int,
        window: Optional[Tuple[int | str, int | str]] = None,
    ) -> VectorSelection:
        """
        Search the top scoring edges according to `query` with no more than `limit` edges

        Args:
          query (str | list): the text or the embedding to score against
          limit (int): the maximum number of new edges to search
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered

        Returns:
          VectorSelection: The vector selection resulting from the search
        """

    def empty_selection(self):
        """Return an empty selection of documents"""

    def entities_by_similarity(
        self,
        query: str | list,
        limit: int,
        window: Optional[Tuple[int | str, int | str]] = None,
    ) -> VectorSelection:
        """
        Search the top scoring entities according to `query` with no more than `limit` entities

        Args:
          query (str | list): the text or the embedding to score against
          limit (int): the maximum number of new entities to search
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered

        Returns:
          VectorSelection: The vector selection resulting from the search
        """

    def nodes_by_similarity(
        self,
        query: str | list,
        limit: int,
        window: Optional[Tuple[int | str, int | str]] = None,
    ) -> VectorSelection:
        """
        Search the top scoring nodes according to `query` with no more than `limit` nodes

        Args:
          query (str | list): the text or the embedding to score against
          limit (int): the maximum number of new nodes to search
          window (Tuple[int | str, int | str], optional): the window where documents need to belong to in order to be considered

        Returns:
          VectorSelection: The vector selection resulting from the search
        """

    def save_embeddings(self, file):
        """Save the embeddings present in this graph to `file` so they can be further used in a call to `vectorise`"""
