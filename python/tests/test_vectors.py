from raphtory import Graph
from raphtory.vectors import VectorisedGraph

embedding_map = {
    "node1": [1.0, 0.0, 0.0],
    "node2": [0.0, 1.0, 0.0],
    "node3": [0.0, 0.0, 1.0],
    "node4": [1.0, 1.0, 0.0],
    "edge1": [1.0, 0.1, 0.0],
    "edge2": [0.0, 1.0, 0.1],
    "edge3": [0.0, 1.0, 1.0],
}


def single_embedding(text: str):
    try:
        return embedding_map[text]
    except:
        raise Exception(f"unexpected document content: {text}")


def embedding(texts):
    return [single_embedding(text) for text in texts]


def floats_are_equals(float1: float, float2: float) -> bool:
    return float1 + 0.001 > float2 and float1 - 0.001 < float2


# the graph generated by this function looks like this (entities labeled with (2d) have 2 documents):
#
#        edge1 (2d)
#      ╭─────── node2
#    node1 (2d)
#      ╰─────── node3  ───── node4
#           edge2             edge3
#
#
def create_graph() -> VectorisedGraph:
    g = Graph()

    g.add_node(1, "node1")
    g.add_node(2, "node2")
    g.add_node(3, "node3")
    g.add_node(4, "node4")

    g.add_edge(2, "node1", "node2", {"name": "edge1"})
    g.add_edge(3, "node1", "node3", {"name": "edge2"})
    g.add_edge(4, "node3", "node4", {"name": "edge3"})

    vg = g.vectorise(
        embedding, node_template="{{ name }}", edge_template="{{ props.name }}"
    )

    return vg


def test_selection():
    vg = create_graph()

    assert len(vg.empty_selection().get_documents()) == 0
    assert len(vg.empty_selection().get_documents_with_scores()) == 0

    nodes_to_select = ["node1", "node2"]
    edges_to_select = [("node1", "node2"), ("node1", "node3")]

    selection = vg.empty_selection()
    selection.add_nodes(nodes_to_select)
    nodes = selection.nodes()
    node_names_returned = [node.name for node in nodes]
    assert node_names_returned == nodes_to_select
    docs = [doc.content for doc in selection.get_documents()]
    assert docs == ["node1", "node2"]

    selection = vg.empty_selection()
    selection.add_edges(edges_to_select)
    edges = selection.edges()
    edge_names_returned = [(edge.src.name, edge.dst.name) for edge in edges]
    assert edge_names_returned == edges_to_select
    docs = [doc.content for doc in selection.get_documents()]
    assert docs == ["edge1", "edge2"]

    edge_tuples = [(edge.src, edge.dst) for edge in edges]
    selection = vg.empty_selection()
    selection.add_nodes(nodes)
    selection.add_edges(edge_tuples)
    nodes_returned = selection.nodes()
    assert nodes == nodes_returned
    edges_returned = selection.edges()
    assert edges == edges_returned


def test_search():
    vg = create_graph()

    assert len(vg.edges_by_similarity("edge1", 10).nodes()) == 0
    assert len(vg.nodes_by_similarity("node1", 10).edges()) == 0

    selection = vg.nodes_by_similarity([1.0, 0.0, 0.0], 1)
    assert [node.name for node in selection.nodes()] == ["node1"]
    assert [doc.content for doc in selection.get_documents()] == ["node1"]

    edges = vg.edges_by_similarity([1.0, 0.0, 0.0], 1).edges()
    edge_names_returned = [(edge.src.name, edge.dst.name) for edge in edges]
    assert edge_names_returned == [("node1", "node2")]
    # TODO: same for edges ?

    (doc1, score1), (doc2, score2) = vg.documents_by_similarity(
        [1.0, 0.0, 0.0], 2
    ).get_documents_with_scores()
    assert floats_are_equals(score1, 1.0)
    assert (doc1.entity.name, doc1.content) == ("node1", "node1")
    assert (doc2.entity.src.name, doc2.entity.dst.name) == ("node1", "node2")

    [(doc1, score1)] = vg.entities_by_similarity(
        [1.0, 0.0, 0.0], 1
    ).get_documents_with_scores()
    assert floats_are_equals(score1, 1.0)
    assert (doc1.entity.name, doc1.content) == ("node1", "node1")

    docs = vg.documents_by_similarity([0.0, 0.0, 1.1], 3).get_documents()
    assert [doc.content for doc in docs] == ["node3", "edge3", "edge2"]

    # chained search
    node_selection = vg.nodes_by_similarity("node2", 1)
    edge_selection = vg.edges_by_similarity("node3", 1)
    entity_selection = vg.entities_by_similarity("node1", 4)
    docs = (
        node_selection.append(edge_selection)
        .append(entity_selection)
        .get_documents()[:4]
    )
    assert [doc.content for doc in docs] == ["node2", "edge3", "node1", "edge1"]
    # the intention of this test was getting all the documents of for different entities,
    # including at least node and one edge at the top.
    # However, we don't have a way currently of taking the documents of the first N entities
    # we could have a method selection.limit_entities()
    # or we could also have a method entity.get_documents for the entities we return (not trivial)


def test_expansion():
    vg = create_graph()

    selection = vg.entities_by_similarity("node1", 1)
    selection.expand(2)
    assert len(selection.get_documents()) == 5
    assert len(selection.nodes()) == 3
    assert len(selection.edges()) == 2

    selection = vg.entities_by_similarity("node1", 1)
    selection.expand_entities_by_similarity("edge1", 1)
    selection.expand_entities_by_similarity("node2", 1)
    assert len(selection.get_documents()) == 3
    nodes = selection.nodes()
    node_names_returned = [node.name for node in nodes]
    assert node_names_returned == ["node1", "node2"]
    edges = selection.edges()
    edge_names_returned = [(edge.src.name, edge.dst.name) for edge in edges]
    assert edge_names_returned == [("node1", "node2")]

    selection = vg.empty_selection()
    selection.expand_entities_by_similarity("node3", 10)
    assert len(selection.get_documents()) == 0

    selection = vg.entities_by_similarity("node1", 1)
    selection.expand_entities_by_similarity("node3", 10)
    assert len(selection.get_documents()) == 7
    assert len(selection.nodes()) == 4
    assert len(selection.edges()) == 3
    # TODO: add some expand_documents here


def test_windows():
    vg = create_graph()

    selection = vg.nodes_by_similarity("node1", 1, (4, 5))
    assert [doc.content for doc in selection.get_documents()] == ["node4"]

    selection = vg.nodes_by_similarity("node4", 1, (1, 2))
    assert [doc.content for doc in selection.get_documents()] == ["node1"]

    selection.expand(10, (0, 3))
    contents = [doc.content for doc in selection.get_documents()]
    assert contents == ["node1", "edge1", "node2"]

    selection.expand_documents_by_similarity("edge2", 100, (0, 4))
    contents = [doc.content for doc in selection.get_documents()]
    assert contents == ["node1", "edge1", "node2", "edge2", "node3"]

    # this should leave the selection unchanged
    selection.expand_documents_by_similarity("node1", 100, (20, 100))
    contents = [doc.content for doc in selection.get_documents()]
    assert contents == ["node1", "edge1", "node2", "edge2", "node3"]

    # this should also leave the selection unchanged
    selection.expand_entities_by_similarity("node1", 100, (20, 100))
    contents = [doc.content for doc in selection.get_documents()]
    assert contents == ["node1", "edge1", "node2", "edge2", "node3"]

    selection.expand(10, (4, 100))
    contents = [doc.content for doc in selection.get_documents()]
    assert contents == ["node1", "edge1", "node2", "edge2", "node3", "edge3", "node4"]


def test_filtering_by_entity_type():
    vg = create_graph()

    selection = vg.empty_selection()
    selection.add_nodes(["node1"])
    selection.expand_nodes_by_similarity("node2", 10)
    contents = [doc.content for doc in selection.get_documents()]
    assert contents == ["node1", "node2", "node3", "node4"]

    selection = vg.empty_selection()
    selection.add_edges([("node1", "node2")])
    selection.expand_edges_by_similarity("edge3", 10)
    contents = [doc.content for doc in selection.get_documents()]
    assert contents == ["edge1", "edge2", "edge3"]


### MULTI-DOCUMENT VERSION TO BE RE-ENABLED

# from raphtory import Graph
# from raphtory.vectors import VectorisedGraph

# embedding_map = {
#     "node1": [1.0, 0.0, 0.0],
#     "node2": [0.0, 1.0, 0.0],
#     "node3": [0.0, 0.0, 1.0],
#     "node4": [1.0, 1.0, 0.0],
#     "edge1": [1.0, 0.1, 0.0],
#     "edge2": [0.0, 1.0, 0.1],
#     "edge3": [0.0, 1.0, 1.0],
#     "node1-extra": [0.0, 1.0, 1.0],
#     "edge1-extra": [0.1, 1.0, 0.0],
# }


# def single_embedding(text: str):
#     try:
#         return embedding_map[text]
#     except:
#         raise Exception(f"unexpected document content: {text}")


# def embedding(texts):
#     return [single_embedding(text) for text in texts]


# def floats_are_equals(float1: float, float2: float) -> bool:
#     return float1 + 0.001 > float2 and float1 - 0.001 < float2


# # the graph generated by this function looks like this (entities labeled with (2d) have 2 documents):
# #
# #        edge1 (2d)
# #      ╭─────── node2
# #    node1 (2d)
# #      ╰─────── node3  ───── node4
# #           edge2             edge3
# #
# #
# def create_graph() -> VectorisedGraph:
#     g = Graph()

#     g.add_node(1, "node1", {"doc": ["node1", "node1-extra"]}) # multi-document node
#     g.add_node(2, "node2", {"doc": ["node2"]})
#     g.add_node(3, "node3", {"doc": ["node3"]})
#     g.add_node(4, "node4", {"doc": ["node4"]})

#     g.add_edge(2, "node1", "node2", {"doc": ["edge1", "edge1-extra"]}) # multi-document edge
#     g.add_edge(3, "node1", "node3", {"doc": ["edge2"]})
#     g.add_edge(4, "node3", "node4", {"doc": ["edge3"]})

#     vg = g.vectorise(embedding, node_document="doc", edge_document="doc")

#     return vg


# def test_selection():
#     vg = create_graph()

#     assert len(vg.empty_selection().get_documents()) == 0
#     assert len(vg.empty_selection().get_documents_with_scores()) == 0

#     nodes_to_select = ["node1", "node2"]
#     edges_to_select = [("node1", "node2"), ("node1", "node3")]

#     selection = vg.empty_selection()
#     selection.add_nodes(nodes_to_select)
#     nodes = selection.nodes()
#     node_names_returned = [node.name for node in nodes]
#     assert node_names_returned == nodes_to_select
#     docs = [doc.content for doc in selection.get_documents()]
#     assert docs == ["node1", "node1-extra", "node2"]

#     selection = vg.empty_selection()
#     selection.add_edges(edges_to_select)
#     edges = selection.edges()
#     edge_names_returned = [(edge.src.name, edge.dst.name) for edge in edges]
#     assert edge_names_returned == edges_to_select
#     docs = [doc.content for doc in selection.get_documents()]
#     assert docs == ["edge1", "edge1-extra", "edge2"]

#     edge_tuples = [(edge.src, edge.dst) for edge in edges]
#     selection = vg.empty_selection()
#     selection.add_nodes(nodes)
#     selection.add_edges(edge_tuples)
#     nodes_returned = selection.nodes()
#     assert nodes == nodes_returned
#     edges_returned = selection.edges()
#     assert edges == edges_returned


# def test_search():
#     vg = create_graph()

#     assert len(vg.edges_by_similarity("edge1", 10).nodes()) == 0
#     assert len(vg.nodes_by_similarity("node1", 10).edges()) == 0

#     selection = vg.nodes_by_similarity([1.0, 0.0, 0.0], 1)
#     assert [node.name for node in selection.nodes()] == ["node1"]
#     assert [doc.content for doc in selection.get_documents()] == ["node1", "node1-extra"]

#     edges = vg.edges_by_similarity([1.0, 0.0, 0.0], 1).edges()
#     edge_names_returned = [(edge.src.name, edge.dst.name) for edge in edges]
#     assert edge_names_returned == [("node1", "node2")]
#     # TODO: same for edges ?

#     (doc1, score1), (doc2, score2) = vg.documents_by_similarity(
#         [1.0, 0.0, 0.0], 2
#     ).get_documents_with_scores()
#     assert floats_are_equals(score1, 1.0)
#     assert (doc1.entity.name, doc1.content) == ("node1", "node1")
#     assert (doc2.entity.src.name, doc2.entity.dst.name) == ("node1", "node2")

#     (doc1, score1), (doc2, score2) = vg.entities_by_similarity(
#         [1.0, 0.0, 0.0], 1
#     ).get_documents_with_scores()
#     assert floats_are_equals(score1, 1.0)
#     assert (doc1.entity.name, doc1.content) == ("node1", "node1")
#     assert (doc2.entity.name, doc2.content) == ("node1", "node1-extra")

#     docs = vg.documents_by_similarity([0.0, 0.0, 1.1], 3).get_documents()
#     assert [doc.content for doc in docs] == ["node3", "node1-extra", "edge3"]

#     # chained search
#     node_selection = vg.nodes_by_similarity("node2", 1);
#     edge_selection = vg.edges_by_similarity("node3", 1);
#     entity_selection = vg.entities_by_similarity("node1", 4);
#     docs = node_selection.join(edge_selection).join(entity_selection).get_documents()[:4]
#     # assert [doc.content for doc in docs] == ['node2', 'edge3', 'node1', 'edge1']
#     assert [doc.content for doc in docs] == ["node2", "edge3", "node1", "node1-extra"]
#     # the intention of this test was getting all the documents of for different entities,
#     # including at least node and one edge at the top.
#     # However, we don't have a way currently of taking the documents of the first N entities
#     # we could have a method selection.limit_entities()
#     # or we could also have a method entity.get_documents for the entities we return (not trivial)


# def test_expansion():
#     vg = create_graph()

#     selection = vg.entities_by_similarity("node1", 1)
#     selection.expand(2)
#     assert len(selection.get_documents()) == 7
#     assert len(selection.nodes()) == 3
#     assert len(selection.edges()) == 2

#     selection = vg.entities_by_similarity("node1", 1)
#     selection.expand_entities_by_similarity("edge1", 1)
#     selection.expand_entities_by_similarity("node2", 1)
#     assert len(selection.get_documents()) == 5
#     nodes = selection.nodes()
#     node_names_returned = [node.name for node in nodes]
#     assert node_names_returned == ["node1", "node2"]
#     edges = selection.edges()
#     edge_names_returned = [(edge.src.name, edge.dst.name) for edge in edges]
#     assert edge_names_returned == [("node1", "node2")]

#     selection = vg.empty_selection()
#     selection.expand_entities_by_similarity("node3", 10)
#     assert len(selection.get_documents()) == 0

#     selection = vg.entities_by_similarity("node1", 1)
#     selection.expand_entities_by_similarity("node3", 10)
#     assert len(selection.get_documents()) == 9
#     assert len(selection.nodes()) == 4
#     assert len(selection.edges()) == 3
#     # TODO: add some expand_documents here


# def test_windows():
#     vg = create_graph()

#     selection = vg.nodes_by_similarity("node1", 1, (4, 5))
#     assert [doc.content for doc in selection.get_documents()] == ["node4"]

#     selection = vg.nodes_by_similarity("node4", 1, (1, 2))
#     assert [doc.content for doc in selection.get_documents()] == ["node1", "node1-extra"]

#     selection.expand(10, (0, 3))
#     contents = [doc.content for doc in selection.get_documents()]
#     assert contents == ["node1", "node1-extra", "edge1", "edge1-extra", "node2"]

#     selection.expand_documents_by_similarity("edge2", 100, (0, 4))
#     contents = [doc.content for doc in selection.get_documents()]
#     assert contents == ["node1", "node1-extra", "edge1", "edge1-extra", "node2", "edge2", "node3"]

#     # this should leave the selection unchanged
#     selection.expand_documents_by_similarity("node1", 100, (20, 100))
#     contents = [doc.content for doc in selection.get_documents()]
#     assert contents == ["node1", "node1-extra", "edge1", "edge1-extra", "node2", "edge2", "node3"]

#     # this should also leave the selection unchanged
#     selection.expand_entities_by_similarity("node1", 100, (20, 100))
#     contents = [doc.content for doc in selection.get_documents()]
#     assert contents == ["node1", "node1-extra", "edge1", "edge1-extra", "node2", "edge2", "node3"]

#     selection.expand(10, (4, 100))
#     contents = [doc.content for doc in selection.get_documents()]
#     assert contents == ["node1", "node1-extra", "edge1", "edge1-extra", "node2", "edge2", "node3", "edge3", "node4"]


# def test_filtering_by_entity_type():
#     vg = create_graph()

#     selection = vg.empty_selection()
#     selection.add_nodes(["node1"])
#     selection.expand_nodes_by_similarity("node2", 10)
#     contents = [doc.content for doc in selection.get_documents()]
#     assert contents == ["node1", "node1-extra", "node2", "node3", "node4"]

#     selection = vg.empty_selection()
#     selection.add_edges([("node1", "node2")])
#     selection.expand_edges_by_similarity("edge3", 10)
#     contents = [doc.content for doc in selection.get_documents()]
#     assert contents == ["edge1", "edge1-extra", "edge2", "edge3"]
