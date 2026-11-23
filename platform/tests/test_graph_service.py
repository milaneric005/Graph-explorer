import pytest

from graph_api import Graph
from graph_platform import (
    DATA_SOURCE_GROUP,
    VISUALIZER_GROUP,
    GraphService,
    GraphServiceError,
    PluginNotFoundError,
)
from plugin_stubs import StubDataSource, StubEntryPoint, StubVisualizer


def test_lists_registered_plugins(graph_service):
    assert {p.identifier() for p in graph_service.data_sources()} == {
        "stub_source", "failing_source", "wrong_result_source",
    }
    assert {p.identifier() for p in graph_service.visualizers()} == {
        "stub_visualizer", "failing_visualizer", "wrong_result_visualizer",
    }


def test_load_graph_returns_graph_from_data_source(graph_service):
    graph = graph_service.load_graph("stub_source", path="graf.json")

    assert isinstance(graph, Graph)
    assert graph.directed
    assert {node.node_id for node in graph.nodes} == {"a", "b"}
    assert [edge.edge_id for edge in graph.edges] == ["e1"]
    assert graph.get_node("a").attributes["age"] == 30


def test_load_graph_passes_params_to_plugin(graph_service, stub_data_source):
    graph_service.load_graph("stub_source", path="graf.json", limit=5)

    assert stub_data_source.received_params == {"path": "graf.json", "limit": 5}


def test_load_graph_optional_param_can_be_omitted(graph_service, stub_data_source):
    graph_service.load_graph("stub_source", path="graf.json")

    assert stub_data_source.received_params == {"path": "graf.json"}


@pytest.mark.parametrize("params", [{}, {"path": None}, {"path": ""}])
def test_load_graph_missing_required_param_raises_error(graph_service, stub_data_source, params):
    with pytest.raises(GraphServiceError, match="path"):
        graph_service.load_graph("stub_source", **params)

    assert stub_data_source.received_params is None


def test_load_graph_unknown_plugin_raises_plugin_not_found(graph_service):
    with pytest.raises(PluginNotFoundError):
        graph_service.load_graph("nepostojeci", path="graf.json")


def test_load_graph_wraps_plugin_error(graph_service):
    with pytest.raises(GraphServiceError) as error_info:
        graph_service.load_graph("failing_source", path="graf.json")

    assert isinstance(error_info.value.__cause__, IOError)


def test_load_graph_rejects_result_that_is_not_graph(graph_service):
    with pytest.raises(GraphServiceError):
        graph_service.load_graph("wrong_result_source", path="graf.json")


def test_render_graph_returns_html_from_visualizer(graph_service, stub_visualizer):
    graph = Graph()

    html = graph_service.render_graph(graph, "stub_visualizer")

    assert html == StubVisualizer.RESULT
    assert stub_visualizer.received_graph is graph


def test_render_graph_unknown_plugin_raises_plugin_not_found(graph_service):
    with pytest.raises(PluginNotFoundError):
        graph_service.render_graph(Graph(), "nepostojeci")


def test_render_graph_wraps_plugin_error(graph_service):
    with pytest.raises(GraphServiceError) as error_info:
        graph_service.render_graph(Graph(), "failing_visualizer")

    assert isinstance(error_info.value.__cause__, RuntimeError)


def test_render_graph_rejects_result_that_is_not_string(graph_service):
    with pytest.raises(GraphServiceError):
        graph_service.render_graph(Graph(), "wrong_result_visualizer")


def test_graph_from_data_source_is_passed_to_visualizer(graph_service, stub_visualizer):
    graph = graph_service.load_graph("stub_source", path="graf.json")

    html = graph_service.render_graph(graph, "stub_visualizer")

    assert html == StubVisualizer.RESULT
    assert stub_visualizer.received_graph is graph


def test_create_default_loads_installed_plugins(fake_entry_points):
    fake_entry_points({
        DATA_SOURCE_GROUP: [StubEntryPoint("stub_source", StubDataSource)],
        VISUALIZER_GROUP: [StubEntryPoint("stub_visualizer", StubVisualizer)],
    })

    service = GraphService.create_default()

    assert [p.identifier() for p in service.data_sources()] == ["stub_source"]
    assert [p.identifier() for p in service.visualizers()] == ["stub_visualizer"]