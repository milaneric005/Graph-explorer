from graph_api import DataSourcePlugin, Edge, Graph, Node, PluginParameter, VisualizerPlugin


class StubDataSource(DataSourcePlugin):
    """Stub data source: uvek vraća isti mali graf (2 čvora, 1 grana) i pamti parametre."""

    def __init__(self) -> None:
        self.received_params = None

    def identifier(self) -> str:
        return "stub_source"

    def name(self) -> str:
        return "Stub source"

    def parameters(self):
        return [
            PluginParameter("path", "Putanja"),
            PluginParameter("limit", "Limit", required=False),
        ]

    def load(self, **params) -> Graph:
        self.received_params = params
        graph = Graph(directed=True)
        node_a = Node("a", {"name": "A", "age": 30})
        node_b = Node("b", {"name": "B"})
        graph.add_node(node_a)
        graph.add_node(node_b)
        graph.add_edge(Edge("e1", node_a, node_b))
        return graph


class FailingDataSource(StubDataSource):
    """Stub data source koji uvek pukne pri učitavanju."""

    def identifier(self) -> str:
        return "failing_source"

    def load(self, **params) -> Graph:
        raise IOError("Fajl ne postoji")


class WrongResultDataSource(StubDataSource):
    """Stub data source koji umesto grafa vraća string."""

    def identifier(self) -> str:
        return "wrong_result_source"

    def load(self, **params):
        return "ovo nije graf"


class StubVisualizer(VisualizerPlugin):
    """Stub visualizer: uvek vraća isti string i pamti graf koji je dobio."""

    RESULT = "<stub-graph></stub-graph>"

    def __init__(self) -> None:
        self.received_graph = None

    def identifier(self) -> str:
        return "stub_visualizer"

    def name(self) -> str:
        return "Stub visualizer"

    def render(self, graph: Graph) -> str:
        self.received_graph = graph
        return self.RESULT


class FailingVisualizer(StubVisualizer):
    """Stub visualizer koji uvek pukne pri prikazu."""

    def identifier(self) -> str:
        return "failing_visualizer"

    def render(self, graph: Graph) -> str:
        raise RuntimeError("Greška pri prikazu")


class WrongResultVisualizer(StubVisualizer):
    """Stub visualizer koji umesto stringa vraća broj."""

    def identifier(self) -> str:
        return "wrong_result_visualizer"

    def render(self, graph: Graph):
        return 42


class StubEntryPoint:
    """Zamena za pravi entry point: umesto importovanja modula vraća zadatu klasu ili baca grešku."""

    def __init__(self, name: str, target=None, error: Exception = None) -> None:
        self.name = name
        self._target = target
        self._error = error

    def load(self):
        if self._error is not None:
            raise self._error
        return self._target