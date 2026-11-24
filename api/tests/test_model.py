from datetime import date

import pytest

from graph_api import Edge, Graph, GraphError, Node


def node_ids(nodes):
    return {node.node_id for node in nodes}


def make_graph(directed, node_names, edge_pairs):
    """Pravi graf od naziva cvorova i parova (izvor, odrediste); id grane je e1, e2, ..."""
    graph = Graph(directed=directed)
    nodes = {name: Node(name) for name in node_names}
    for node in nodes.values():
        graph.add_node(node)
    for i, (source, target) in enumerate(edge_pairs, start=1):
        graph.add_edge(Edge(f"e{i}", nodes[source], nodes[target]))
    return graph


# ---------- tipovi vrednosti atributa ----------

@pytest.mark.parametrize("value", [25, 1.75, "Alice", date(2000, 3, 1)])
def test_attribute_keeps_its_type(value):
    node = Node("1", {"x": value})

    assert node.attributes["x"] == value
    assert type(node.attributes["x"]) is type(value)


def test_attributes_are_not_converted_to_strings():
    node = Node("1", {"Age": 25, "Height": 160.5, "Born": date(2000, 3, 1)})

    assert isinstance(node.attributes["Age"], int)
    assert isinstance(node.attributes["Height"], float)
    assert isinstance(node.attributes["Born"], date)


@pytest.mark.parametrize("value", [True, None, [1, 2], {"a": 1}, (1, 2), object()])
def test_unsupported_attribute_type_is_rejected(value):
    with pytest.raises(TypeError):
        Node("1", {"x": value})


def test_set_attribute_rejects_unsupported_type():
    node = Node("1")

    with pytest.raises(TypeError):
        node.set_attribute("x", [1])


def test_edge_attributes_are_typed_too():
    a, b = Node("a"), Node("b")

    edge = Edge("e1", a, b, {"Weight": 2.5})

    assert edge.attributes["Weight"] == 2.5
    with pytest.raises(TypeError):
        Edge("e2", a, b, {"Weight": None})


def test_set_get_remove_attribute():
    node = Node("1")

    node.set_attribute("Age", 25)
    assert node.get_attribute("Age") == 25

    node.set_attribute("Age", 26)
    assert node.get_attribute("Age") == 26

    node.remove_attribute("Age")
    assert node.get_attribute("Age") is None
    assert node.get_attribute("Age", 0) == 0


def test_remove_missing_attribute_does_not_fail():
    Node("1").remove_attribute("missing")


# ---------- cvorovi ----------

def test_add_and_get_node():
    graph = Graph()
    node = Node("1")

    graph.add_node(node)

    assert graph.has_node("1")
    assert graph.get_node("1") is node
    assert graph.nodes == [node]


def test_get_missing_node_returns_none():
    graph = Graph()

    assert graph.get_node("x") is None
    assert not graph.has_node("x")


def test_add_node_with_existing_id_raises():
    graph = Graph()
    graph.add_node(Node("1"))

    with pytest.raises(GraphError):
        graph.add_node(Node("1"))


def test_remove_node():
    graph = Graph()
    graph.add_node(Node("1"))

    graph.remove_node("1")

    assert not graph.has_node("1")
    assert graph.nodes == []


def test_remove_missing_node_raises():
    with pytest.raises(GraphError):
        Graph().remove_node("x")


def test_remove_node_with_edges_raises_until_edges_are_removed():
    graph = make_graph(True, ["a", "b"], [("a", "b")])

    with pytest.raises(GraphError):
        graph.remove_node("a")
    with pytest.raises(GraphError):
        graph.remove_node("b")
    assert graph.has_node("a")

    graph.remove_edge("e1")
    graph.remove_node("a")

    assert not graph.has_node("a")


def test_nodes_property_returns_copy():
    graph = Graph()
    graph.add_node(Node("1"))

    graph.nodes.clear()

    assert len(graph.nodes) == 1


# ---------- grane ----------

def test_add_and_get_edge():
    graph = Graph()
    a, b = Node("a"), Node("b")
    graph.add_node(a)
    graph.add_node(b)
    edge = Edge("e1", a, b)

    graph.add_edge(edge)

    assert graph.get_edge("e1") is edge
    assert graph.edges == [edge]


def test_get_missing_edge_returns_none():
    assert Graph().get_edge("x") is None


def test_add_edge_with_existing_id_raises():
    graph = make_graph(True, ["a", "b"], [("a", "b")])
    a, b = graph.get_node("a"), graph.get_node("b")

    with pytest.raises(GraphError):
        graph.add_edge(Edge("e1", b, a))


@pytest.mark.parametrize("missing", ["source", "target"])
def test_add_edge_with_node_outside_graph_raises(missing):
    graph = Graph()
    a, outsider = Node("a"), Node("outsider")
    graph.add_node(a)
    source, target = (outsider, a) if missing == "source" else (a, outsider)

    with pytest.raises(GraphError):
        graph.add_edge(Edge("e1", source, target))

    assert graph.edges == []


def test_remove_edge():
    graph = make_graph(True, ["a", "b"], [("a", "b")])

    graph.remove_edge("e1")

    assert graph.get_edge("e1") is None
    assert graph.edges == []
    assert graph.has_node("a") and graph.has_node("b")


def test_remove_missing_edge_raises():
    with pytest.raises(GraphError):
        Graph().remove_edge("x")


def test_edges_of_returns_incoming_and_outgoing_edges():
    graph = make_graph(True, ["a", "b", "c"], [("a", "b"), ("c", "a"), ("b", "c")])

    assert {e.edge_id for e in graph.edges_of("a")} == {"e1", "e2"}
    assert {e.edge_id for e in graph.edges_of("b")} == {"e1", "e3"}
    assert graph.edges_of("unknown") == []


def test_edges_property_returns_copy():
    graph = make_graph(True, ["a", "b"], [("a", "b")])

    graph.edges.clear()

    assert len(graph.edges) == 1


# ---------- vrste grafova ----------

def test_directed_flag():
    assert Graph().directed is True
    assert Graph(directed=True).directed is True
    assert Graph(directed=False).directed is False


def test_acyclic_graph():
    graph = make_graph(True, ["a", "b", "c"], [("a", "b"), ("b", "c")])

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2


def test_cyclic_graph_with_cycle_between_two_nodes():
    graph = make_graph(True, ["a", "b"], [("a", "b"), ("b", "a")])

    assert len(graph.edges) == 2
    assert node_ids(graph.neighbors("a")) == {"b"}
    assert node_ids(graph.neighbors("b")) == {"a"}


def test_cyclic_graph_with_longer_cycle():
    graph = make_graph(True, ["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])

    assert node_ids(graph.neighbors("c")) == {"a"}


def test_self_loop_is_allowed():
    graph = make_graph(True, ["a"], [("a", "a")])

    assert len(graph.edges) == 1
    assert node_ids(graph.neighbors("a")) == {"a"}
    assert len(graph.edges_of("a")) == 1


def test_parallel_edges_are_distinct():
    graph = make_graph(True, ["a", "b"], [("a", "b"), ("a", "b")])

    assert len(graph.edges) == 2
    assert [n.node_id for n in graph.neighbors("a")] == ["b"]  # bez duplikata

    graph.remove_edge("e1")

    assert graph.get_edge("e2") is not None


def test_disconnected_graph():
    graph = make_graph(False, ["a", "b", "c", "d", "lonely"], [("a", "b"), ("c", "d")])

    assert len(graph.nodes) == 5
    assert graph.neighbors("lonely") == []
    assert node_ids(graph.neighbors("a")) == {"b"}
    assert node_ids(graph.neighbors("c")) == {"d"}


def test_graph_without_edges_and_empty_graph():
    graph = Graph()
    assert graph.nodes == [] and graph.edges == []

    graph.add_node(Node("1"))
    assert graph.edges == []


# ---------- neighbors ----------

def test_neighbors_directed_returns_only_outgoing():
    graph = make_graph(True, ["a", "b", "c"], [("a", "b"), ("c", "a")])

    assert node_ids(graph.neighbors("a")) == {"b"}
    assert node_ids(graph.neighbors("b")) == set()
    assert node_ids(graph.neighbors("c")) == {"a"}


def test_neighbors_undirected_returns_both_directions():
    graph = make_graph(False, ["a", "b", "c"], [("a", "b"), ("c", "a")])

    assert node_ids(graph.neighbors("a")) == {"b", "c"}
    assert node_ids(graph.neighbors("b")) == {"a"}
    assert node_ids(graph.neighbors("c")) == {"a"}


def test_neighbors_of_unknown_node_raises():
    with pytest.raises(GraphError):
        Graph().neighbors("x")


# ---------- subgraph ----------

def test_subgraph_keeps_given_nodes_and_edges_between_them():
    graph = make_graph(True, ["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])

    sub = graph.subgraph(["a", "b"])

    assert node_ids(sub.nodes) == {"a", "b"}
    assert {e.edge_id for e in sub.edges} == {"e1"}


def test_subgraph_ignores_unknown_ids():
    graph = make_graph(True, ["a", "b"], [("a", "b")])

    sub = graph.subgraph(["a", "unknown"])

    assert node_ids(sub.nodes) == {"a"}
    assert sub.edges == []


def test_subgraph_keeps_directed_flag():
    assert Graph(directed=False).subgraph([]).directed is False
    assert Graph(directed=True).subgraph([]).directed is True


def test_subgraph_does_not_change_original_graph():
    graph = make_graph(True, ["a", "b"], [("a", "b")])

    sub = graph.subgraph(["a"])
    sub.remove_node("a")

    assert graph.has_node("a")
    assert len(graph.edges) == 1


def test_subgraph_of_subgraph():
    graph = make_graph(True, ["a", "b", "c"], [("a", "b"), ("b", "c")])

    sub = graph.subgraph(["a", "b", "c"]).subgraph(["b", "c"])

    assert node_ids(sub.nodes) == {"b", "c"}
    assert {e.edge_id for e in sub.edges} == {"e2"}
    
# ---------- clear ----------

def test_clear_removes_everything():
    graph = make_graph(True, ["a", "b"], [("a", "b")])

    graph.clear()

    assert graph.nodes == []
    assert graph.edges == []
    graph.add_node(Node("a"))  # id je opet slobodan