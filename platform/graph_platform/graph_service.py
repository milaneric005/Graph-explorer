from typing import List, Optional

from graph_api import DataSourcePlugin, Graph, VisualizerPlugin

from .plugin_loader import PluginLoader

from .search import search_graph


class GraphServiceError(Exception):
    """Baca se kada učitavanje ili prikaz grafa ne uspe."""


class GraphService:
    """Jedinstvena tačka preko koje aplikacija komunicira sa plugin-ima.

    Aplikacija (Django, Flask, CLI) ne poziva plugin-e direktno, nego samo
    ovaj servis: on bira plugin po identifikatoru, proverava parametre,
    poziva plugin i proverava ono što je plugin vratio.
    """

    def __init__(self, plugin_loader: Optional[PluginLoader] = None) -> None:
        self._plugin_loader = plugin_loader if plugin_loader is not None else PluginLoader()

    @classmethod
    def create_default(cls) -> "GraphService":
        """Pravi servis koji odmah učitava sve instalirane plugin-e."""
        plugin_loader = PluginLoader()
        plugin_loader.load_plugins()
        return cls(plugin_loader)

    @property
    def plugin_loader(self) -> PluginLoader:
        return self._plugin_loader

    def data_sources(self) -> List[DataSourcePlugin]:
        return self._plugin_loader.data_sources

    def visualizers(self) -> List[VisualizerPlugin]:
        return self._plugin_loader.visualizers

    def load_graph(self, data_source_id: str, **params) -> Graph:
        """Učitava graf preko data source plugin-a sa datim identifikatorom.

        Baca PluginNotFoundError ako plugin ne postoji, a GraphServiceError
        ako fali obavezan parametar, ako plugin pukne ili ne vrati Graph.
        """
        plugin = self._plugin_loader.get_data_source(data_source_id)

        missing = [
            parameter.name
            for parameter in plugin.parameters()
            if parameter.required and params.get(parameter.name) in (None, "")
        ]
        if missing:
            raise GraphServiceError(
                f"Nedostaju obavezni parametri za '{data_source_id}': {', '.join(missing)}"
            )

        try:
            graph = plugin.load(**params)
        except Exception as error:
            raise GraphServiceError(
                f"Data source '{data_source_id}' nije uspeo da učita graf: {error}"
            ) from error

        if not isinstance(graph, Graph):
            raise GraphServiceError(
                f"Data source '{data_source_id}' nije vratio objekat klase Graph."
            )
        return graph

    def render_graph(self, graph: Graph, visualizer_id: str) -> str:
        """Vraća HTML prikaz grafa koji pravi visualizer plugin sa datim identifikatorom.

        Baca PluginNotFoundError ako plugin ne postoji, a GraphServiceError
        ako plugin pukne ili ne vrati string.
        """
        plugin = self._plugin_loader.get_visualizer(visualizer_id)

        try:
            html = plugin.render(graph)
        except Exception as error:
            raise GraphServiceError(
                f"Visualizer '{visualizer_id}' nije uspeo da prikaže graf: {error}"
            ) from error

        if not isinstance(html, str):
            raise GraphServiceError(
                f"Visualizer '{visualizer_id}' nije vratio string."
            )
        return html

    
    def search(self, graph: Graph, query: str) -> Graph:
        """Vraća podgraf čiji čvorovi sadrže upit u nazivu ili vrednosti atributa."""
        return search_graph(graph, query)