from datetime import date

import pytest

from graph_api import Edge, Graph, Node
from graph_platform import GraphService, PluginLoader
from plugin_stubs import (
    FailingDataSource,
    FailingVisualizer,
    StubDataSource,
    StubVisualizer,
    WrongResultDataSource,
    WrongResultVisualizer,
)


@pytest.fixture
def people_graph():
    """Usmeren, cikličan graf od 4 osobe sa atributima svih tipova (str, int, float, date).

    Grane: alice->tom, tom->alice (ciklus), tom->bob, bob->ana.
    Čvor "ana" nema atribute Height ni Born.
    """
    graph = Graph(directed=True)
    alice = Node("alice", {"Name": "Alice", "Age": 25, "Height": 160.5, "Born": date(2000, 3, 1)})
    tom = Node("tom", {"Name": "Tom", "Age": 30, "Height": 175.0, "Born": date(1995, 7, 15)})
    bob = Node("bob", {"Name": "Bob", "Age": 45, "Height": 182.3, "Born": date(1980, 1, 20)})
    ana = Node("ana", {"Name": "Ana", "Age": 30, "City": "Novi Sad"})
    for node in (alice, tom, bob, ana):
        graph.add_node(node)
    graph.add_edge(Edge("e1", alice, tom, {"Relation": "friend"}))
    graph.add_edge(Edge("e2", tom, alice, {"Relation": "friend"}))
    graph.add_edge(Edge("e3", tom, bob))
    graph.add_edge(Edge("e4", bob, ana))
    return graph


@pytest.fixture
def stub_data_source():
    return StubDataSource()


@pytest.fixture
def stub_visualizer():
    return StubVisualizer()


@pytest.fixture
def plugin_loader(stub_data_source, stub_visualizer):
    """PluginLoader u koji su ručno registrovani svi Stub plugin-i."""
    loader = PluginLoader()
    loader.register_data_source(stub_data_source)
    loader.register_data_source(FailingDataSource())
    loader.register_data_source(WrongResultDataSource())
    loader.register_visualizer(stub_visualizer)
    loader.register_visualizer(FailingVisualizer())
    loader.register_visualizer(WrongResultVisualizer())
    return loader


@pytest.fixture
def graph_service(plugin_loader):
    return GraphService(plugin_loader)


@pytest.fixture
def fake_entry_points(monkeypatch):
    """Zamenjuje pretragu instaliranih plugin-a zadatim Stub entry point-ima.

    Poziva se sa rečnikom {ime_grupe: [StubEntryPoint, ...]}.
    """
    def install(groups):
        monkeypatch.setattr(
            PluginLoader,
            "_entry_points",
            staticmethod(lambda group: groups.get(group, [])),
        )
    return install