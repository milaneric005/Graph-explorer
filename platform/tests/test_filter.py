from datetime import date

import pytest

from graph_platform import FilterCondition, FilterError, filter_graph, parse_filter, search_graph


def node_ids(graph):
    return {node.node_id for node in graph.nodes}


def edge_ids(graph):
    return {edge.edge_id for edge in graph.edges}


# ---------- parsiranje upita ----------

@pytest.mark.parametrize("query, expected", [
    ("Age == 30", FilterCondition("Age", "==", "30")),
    ("Age!=30", FilterCondition("Age", "!=", "30")),
    ("Age > 30", FilterCondition("Age", ">", "30")),
    ("Age>=30", FilterCondition("Age", ">=", "30")),
    ("Age < 30", FilterCondition("Age", "<", "30")),
    ("Age <= 30", FilterCondition("Age", "<=", "30")),
    ("Name == 'Tom'", FilterCondition("Name", "==", "Tom")),
    ('City == "Novi Sad"', FilterCondition("City", "==", "Novi Sad")),
])
def test_parse_single_condition(query, expected):
    assert parse_filter(query) == [expected]


def test_parse_multiple_conditions():
    assert parse_filter("Age > 30 && Height >= 150") == [
        FilterCondition("Age", ">", "30"),
        FilterCondition("Height", ">=", "150"),
    ]


@pytest.mark.parametrize("query", [
    "",
    "   ",
    None,
    "Age",                 # nema komparatora ni vrednosti
    "Age 30",              # nema komparatora
    "Age = 30",            # "=" nije podržan komparator
    "Age >",               # nema vrednosti
    "> 30",                # nema naziva atributa
    "Age > 30 &&",         # prazan drugi uslov
])
def test_parse_invalid_query_raises_error(query):
    with pytest.raises(FilterError):
        parse_filter(query)


# ---------- poređenje prema tipu atributa ----------

@pytest.mark.parametrize("query, expected", [
    ("Age == 30", {"tom", "ana"}),
    ("Age != 30", {"alice", "bob"}),
    ("Age > 30", {"bob"}),
    ("Age >= 30", {"tom", "bob", "ana"}),
    ("Age < 30", {"alice"}),
    ("Age <= 30", {"alice", "tom", "ana"}),
])
def test_filter_int_all_comparators(people_graph, query, expected):
    assert node_ids(filter_graph(people_graph, query)) == expected


def test_filter_int_compares_numerically_not_lexicographically(people_graph):
    # leksikografski bi "45" < "5", a numerički je 45 > 5
    assert node_ids(filter_graph(people_graph, "Age > 5")) == {"alice", "tom", "bob", "ana"}


def test_filter_int_attribute_with_decimal_value(people_graph):
    assert node_ids(filter_graph(people_graph, "Age > 29.5")) == {"tom", "bob", "ana"}


def test_filter_float(people_graph):
    assert node_ids(filter_graph(people_graph, "Height >= 175")) == {"tom", "bob"}
    assert node_ids(filter_graph(people_graph, "Height == 160.5")) == {"alice"}


def test_filter_date(people_graph):
    assert node_ids(filter_graph(people_graph, "Born < 1996-01-01")) == {"tom", "bob"}
    assert node_ids(filter_graph(people_graph, "Born == 2000-03-01")) == {"alice"}


def test_filter_string(people_graph):
    assert node_ids(filter_graph(people_graph, "Name == Tom")) == {"tom"}
    assert node_ids(filter_graph(people_graph, "City == 'Novi Sad'")) == {"ana"}
    assert node_ids(filter_graph(people_graph, "Name < B")) == {"alice", "ana"}


def test_filter_skips_nodes_without_attribute(people_graph):
    # "ana" nema atribut Height, pa ne ulazi ni u jedan rezultat
    assert "ana" not in node_ids(filter_graph(people_graph, "Height > 0"))
    assert "ana" not in node_ids(filter_graph(people_graph, "Height != 0"))


def test_filter_unknown_attribute_returns_empty_graph(people_graph):
    result = filter_graph(people_graph, "Weight > 10")

    assert node_ids(result) == set()
    assert edge_ids(result) == set()


def test_filter_multiple_conditions_must_all_match(people_graph):
    result = filter_graph(people_graph, "Age >= 30 && Height < 180")

    assert node_ids(result) == {"tom"}


# ---------- greške tipa ----------

@pytest.mark.parametrize("query", [
    "Age > abc",           # int
    "Height <= visok",     # float
    "Born < 2020",         # date bez meseca i dana
    "Born == 15.07.1995",  # date u pogrešnom formatu
])
def test_filter_wrong_value_type_raises_error(people_graph, query):
    with pytest.raises(FilterError, match="nije odgovarajućeg tipa"):
        filter_graph(people_graph, query)


def test_filter_type_error_is_reported_even_if_previous_condition_fails(people_graph):
    with pytest.raises(FilterError, match="Height"):
        filter_graph(people_graph, "Age > 100 && Height > visok")


def test_filter_error_is_value_error():
    assert issubclass(FilterError, ValueError)


# ---------- podgraf ----------

def test_filter_keeps_only_edges_between_selected_nodes(people_graph):
    result = filter_graph(people_graph, "Age >= 30")   # tom, bob, ana

    assert edge_ids(result) == {"e3", "e4"}


def test_filter_keeps_cycle(people_graph):
    result = filter_graph(people_graph, "Age <= 30")   # alice, tom, ana

    assert {"e1", "e2"} <= edge_ids(result)


def test_filter_does_not_change_original_graph(people_graph):
    result = filter_graph(people_graph, "Age > 30")

    assert result is not people_graph
    assert len(people_graph.nodes) == 4
    assert len(people_graph.edges) == 4
    assert people_graph.get_node("alice").attributes["Born"] == date(2000, 3, 1)


def test_filter_keeps_direction_of_graph(people_graph):
    assert filter_graph(people_graph, "Age > 0").directed is True


# ---------- sukcesivna primena (G1 -> filter -> G2 -> search -> G3 -> filter -> G4) ----------

def test_filter_and_search_can_be_combined_successively(people_graph):
    g2 = filter_graph(people_graph, "Age >= 30")   # tom, bob, ana
    g3 = search_graph(g2, "Height")                # tom, bob
    g4 = filter_graph(g3, "Height > 180")          # bob

    assert node_ids(g2) == {"tom", "bob", "ana"}
    assert node_ids(g3) == {"tom", "bob"}
    assert node_ids(g4) == {"bob"}
    assert node_ids(people_graph) == {"alice", "tom", "bob", "ana"}


# ---------- preko GraphService ----------

def test_graph_service_filter_returns_subgraph(graph_service, people_graph):
    assert node_ids(graph_service.filter(people_graph, "Age > 30")) == {"bob"}


def test_graph_service_filter_raises_filter_error(graph_service, people_graph):
    with pytest.raises(FilterError):
        graph_service.filter(people_graph, "Age > abc")