import pytest

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