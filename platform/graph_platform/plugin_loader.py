import logging
from importlib.metadata import entry_points
from typing import Dict, List, Type, TypeVar

from graph_api import DataSourcePlugin, Plugin, VisualizerPlugin

DATA_SOURCE_GROUP = "graph.data_source"
VISUALIZER_GROUP = "graph.visualizer"

logger = logging.getLogger(__name__)

P = TypeVar("P", bound=Plugin)


class PluginNotFoundError(Exception):
    """Baca se kada plugin sa traženim identifikatorom nije učitan."""


class PluginLoader:
    """Otkriva instalirane plugin-e preko entry point-a i čuva ih po identifikatoru."""

    def __init__(self) -> None:
        self._data_sources: Dict[str, DataSourcePlugin] = {}
        self._visualizers: Dict[str, VisualizerPlugin] = {}

    def load_plugins(self) -> None:
        """Pronalazi i učitava sve instalirane data source i visualizer plugin-e."""
        self._data_sources = self._load_group(DATA_SOURCE_GROUP, DataSourcePlugin)
        self._visualizers = self._load_group(VISUALIZER_GROUP, VisualizerPlugin)

    def register_data_source(self, plugin: DataSourcePlugin) -> None:
        """Ručno registruje data source plugin (koristi se u testovima sa Stub objektima)."""
        self._register(self._data_sources, plugin, DataSourcePlugin)

    def register_visualizer(self, plugin: VisualizerPlugin) -> None:
        """Ručno registruje visualizer plugin (koristi se u testovima sa Stub objektima)."""
        self._register(self._visualizers, plugin, VisualizerPlugin)

    @property
    def data_sources(self) -> List[DataSourcePlugin]:
        return list(self._data_sources.values())

    @property
    def visualizers(self) -> List[VisualizerPlugin]:
        return list(self._visualizers.values())

    def get_data_source(self, identifier: str) -> DataSourcePlugin:
        return self._get(self._data_sources, identifier, "Data source")

    def get_visualizer(self, identifier: str) -> VisualizerPlugin:
        return self._get(self._visualizers, identifier, "Visualizer")

    @staticmethod
    def _entry_points(group: str):
        eps = entry_points()
        if hasattr(eps, "select"):
            return eps.select(group=group)
        return eps.get(group, [])

    def _load_group(self, group: str, base_class: Type[P]) -> Dict[str, P]:
        plugins: Dict[str, P] = {}
        for entry_point in self._entry_points(group):
            try:
                plugin_class = entry_point.load()
            except Exception:
                logger.exception("Plugin '%s' nije moguće učitati.", entry_point.name)
                continue

            if not (isinstance(plugin_class, type) and issubclass(plugin_class, base_class)):
                logger.warning(
                    "Plugin '%s' ne nasleđuje %s i biće preskočen.",
                    entry_point.name, base_class.__name__,
                )
                continue

            try:
                self._register(plugins, plugin_class(), base_class)
            except ValueError as error:
                logger.warning("%s", error)
        return plugins

    @staticmethod
    def _register(registry: Dict[str, P], plugin: P, base_class: Type[P]) -> None:
        if not isinstance(plugin, base_class):
            raise TypeError(f"Plugin mora biti instanca klase {base_class.__name__}.")
        identifier = plugin.identifier()
        if identifier in registry:
            raise ValueError(f"Plugin sa identifikatorom '{identifier}' je već registrovan.")
        registry[identifier] = plugin

    @staticmethod
    def _get(registry: Dict[str, P], identifier: str, kind: str) -> P:
        try:
            return registry[identifier]
        except KeyError:
            raise PluginNotFoundError(f"{kind} plugin '{identifier}' nije pronađen.") from None