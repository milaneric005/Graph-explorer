import pytest

from graph_platform import (
    DATA_SOURCE_GROUP,
    VISUALIZER_GROUP,
    PluginLoader,
    PluginNotFoundError,
)
from plugin_stubs import StubDataSource, StubEntryPoint, StubVisualizer


def test_load_plugins_discovers_installed_plugins(fake_entry_points):
    fake_entry_points({
        DATA_SOURCE_GROUP: [StubEntryPoint("stub_source", StubDataSource)],
        VISUALIZER_GROUP: [StubEntryPoint("stub_visualizer", StubVisualizer)],
    })
    loader = PluginLoader()
    loader.load_plugins()

    assert [p.identifier() for p in loader.data_sources] == ["stub_source"]
    assert [p.identifier() for p in loader.visualizers] == ["stub_visualizer"]
    assert isinstance(loader.get_data_source("stub_source"), StubDataSource)
    assert isinstance(loader.get_visualizer("stub_visualizer"), StubVisualizer)


def test_load_plugins_without_installed_plugins(fake_entry_points):
    fake_entry_points({})
    loader = PluginLoader()
    loader.load_plugins()

    assert loader.data_sources == []
    assert loader.visualizers == []


def test_load_plugins_skips_plugin_that_cannot_be_imported(fake_entry_points):
    fake_entry_points({
        DATA_SOURCE_GROUP: [
            StubEntryPoint("broken", error=ImportError("Modul ne postoji")),
            StubEntryPoint("stub_source", StubDataSource),
        ],
    })
    loader = PluginLoader()
    loader.load_plugins()

    assert [p.identifier() for p in loader.data_sources] == ["stub_source"]


def test_load_plugins_skips_class_with_wrong_base(fake_entry_points):
    fake_entry_points({
        DATA_SOURCE_GROUP: [StubEntryPoint("wrong_group", StubVisualizer)],
        VISUALIZER_GROUP: [StubEntryPoint("not_a_class", "nije klasa")],
    })
    loader = PluginLoader()
    loader.load_plugins()

    assert loader.data_sources == []
    assert loader.visualizers == []


def test_load_plugins_skips_duplicate_identifier(fake_entry_points):
    fake_entry_points({
        DATA_SOURCE_GROUP: [
            StubEntryPoint("first", StubDataSource),
            StubEntryPoint("second", StubDataSource),
        ],
    })
    loader = PluginLoader()
    loader.load_plugins()

    assert len(loader.data_sources) == 1


def test_register_and_get_plugins():
    loader = PluginLoader()
    data_source = StubDataSource()
    visualizer = StubVisualizer()
    loader.register_data_source(data_source)
    loader.register_visualizer(visualizer)

    assert loader.get_data_source("stub_source") is data_source
    assert loader.get_visualizer("stub_visualizer") is visualizer


def test_register_wrong_type_raises_type_error():
    loader = PluginLoader()

    with pytest.raises(TypeError):
        loader.register_data_source(StubVisualizer())
    with pytest.raises(TypeError):
        loader.register_visualizer(StubDataSource())


def test_register_duplicate_identifier_raises_value_error():
    loader = PluginLoader()
    loader.register_data_source(StubDataSource())

    with pytest.raises(ValueError):
        loader.register_data_source(StubDataSource())


def test_get_unknown_plugin_raises_plugin_not_found():
    loader = PluginLoader()

    with pytest.raises(PluginNotFoundError):
        loader.get_data_source("nepostojeci")
    with pytest.raises(PluginNotFoundError):
        loader.get_visualizer("nepostojeci")