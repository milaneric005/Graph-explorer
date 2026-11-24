import pytest

from graph_api import Graph
from graph_platform import search_graph


def node_ids(graph):
    return {node.node_id for node in graph.nodes}


def edge_ids(graph):
    return {edge.edge_id for edge in graph.edges}


def test_search_matches_attribute_value(people_graph):
    result = search_graph(people_graph, "Tom")

    assert node_ids(result) == {"tom"}


@pytest.mark.parametrize("query, expected", [
    ("lic", {"alice"}),            # deo vrednosti "Alice"
    ("Sad", {"ana"}),              # deo vrednosti "Novi Sad"
    ("orn", {"alice", "tom", "bob"}), # deo naziva atributa "Born"
])
def test_search_matches_part_of_name_or_value(people_graph, query, expected):
    assert node_ids(search_graph(people_graph, query)) == expected


def test_search_matches_attribute_name(people_graph):
    result = search_graph(people_graph, "City")

    assert node_ids(result) == {"ana"}


def test_search_is_case_insensitive(people_graph):
    assert node_ids(search_graph(people_graph, "aLiCe")) == {"alice"}
    assert node_ids(search_graph(people_graph, "height")) == {"alice", "tom", "bob"}


@pytest.mark.parametrize("query, expected", [
    ("45", {"bob"}),               # int
    ("160.5", {"alice"}),          # float
    ("1995-07", {"tom"}),          # date
])
def test_search_matches_non_string_values(people_graph, query, expected):
    assert node_ids(search_graph(people_graph, query)) == expected


def test_search_keeps_only_edges_between_found_nodes(people_graph):
    result = search_graph(people_graph, "Height")

    assert node_ids(result) == {"alice", "tom", "bob"}
    assert edge_ids(result) == {"e1", "e2", "e3"}


def test_search_keeps_cycle_between_found_nodes(people_graph):
    result = search_graph(people_graph, "Born")    # alice, tom, bob

    assert {"e1", "e2"} <= edge_ids(result)        # alice->tom i tom->alice


def test_search_does_not_match_edge_attributes(people_graph):
    # "friend" je vrednost atributa grane, a pretraga gleda samo čvorove
    assert node_ids(search_graph(people_graph, "friend")) == set()


def test_search_without_match_returns_empty_graph(people_graph):
    result = search_graph(people_graph, "nepostojece")

    assert node_ids(result) == set()
    assert edge_ids(result) == set()


@pytest.mark.parametrize("query", ["", "   ", None])
def test_empty_query_returns_whole_graph(people_graph, query):
    result = search_graph(people_graph, query)

    assert node_ids(result) == node_ids(people_graph)
    assert edge_ids(result) == edge_ids(people_graph)


def test_search_returns_new_graph_and_does_not_change_original(people_graph):
    result = search_graph(people_graph, "Tom")

    assert result is not people_graph
    assert len(people_graph.nodes) == 4
    assert len(people_graph.edges) == 4


def test_search_keeps_direction_of_graph():
    undirected = Graph(directed=False)

    assert search_graph(undirected, "x").directed is False


def test_search_can_be_applied_successively(people_graph):
    first = search_graph(people_graph, "Age")       # svi
    second = search_graph(first, "Born")           # alice, tom, bob
    third = search_graph(second, "ob")             # bob

    assert node_ids(first) == {"alice", "tom", "bob", "ana"}
    assert node_ids(second) == {"alice", "tom", "bob"}
    assert node_ids(third) == {"bob"}
    assert edge_ids(second) == {"e1", "e2", "e3"}
    assert edge_ids(third) == set()


def test_graph_service_search_returns_subgraph(graph_service, people_graph):
    assert node_ids(graph_service.search(people_graph, "Tom")) == {"tom"}