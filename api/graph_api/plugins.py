from abc import ABC, abstractmethod
from dataclasses import dataclass
from html import escape
from typing import List

from .model import Edge, Graph, Node


class Plugin(ABC):
    """Base class of all plugins. Subclasses need a constructor without arguments."""

    @abstractmethod
    def identifier(self) -> str:
        """Unique id of the plugin, e.g. "json_source"."""

    @abstractmethod
    def name(self) -> str:
        """Name shown to the user in the UI, e.g. "JSON"."""


@dataclass(frozen=True)
class PluginParameter:
    """One input parameter a data source plugin needs from the user."""
    name: str          # e.g. "file_path"
    label: str         # e.g. "Path to file"
    required: bool = True


class DataSourcePlugin(Plugin):
    """Parses a data source and builds a Graph."""

    @abstractmethod
    def parameters(self) -> List[PluginParameter]:
        """Parameters the user has to provide before load() is called."""

    @abstractmethod
    def load(self, **params) -> Graph:
        """Parse the source described by `params` and return the graph."""


class VisualizerPlugin(Plugin):
    """Turns a Graph into an HTML/SVG string that the platform inserts into the page.

    Two ways to implement a visualizer:

    1. Minimal: implement only identifier() and name(), and override
       render_node() (and optionally render_edge()). The default render()
       wraps every node and edge in an element with data-node-id /
       data-edge-id (edges also data-source / data-target) attributes; the
       platform uses them for layout, pan, zoom, drag and drop, selection
       and mouseover.
    2. Full control: override render() and return any markup you want.
    """

    def render_node(self, node: Node) -> str:
        """Markup for the inside of one node (default: a circle with the node id)."""
        return (f'<circle class="node-shape" r="20"></circle>'
                f'<text class="node-label" text-anchor="middle">{escape(str(node.node_id))}</text>')

    def render_edge(self, edge: Edge) -> str:
        """Markup for the inside of one edge (default: a plain line)."""
        return '<line class="edge-line"></line>'

    def render(self, graph: Graph) -> str:
        """HTML/SVG string for the whole graph."""
        edges = "".join(
            f'<g class="edge" data-edge-id="{escape(str(e.edge_id))}" '
            f'data-source="{escape(str(e.source.node_id))}" '
            f'data-target="{escape(str(e.target.node_id))}">{self.render_edge(e)}</g>'
            for e in graph.edges
        )
        nodes = "".join(
            f'<g class="node" data-node-id="{escape(str(n.node_id))}">{self.render_node(n)}</g>'
            for n in graph.nodes
        )
        return (f'<g class="graph" data-directed="{str(graph.directed).lower()}">'
                f'<g class="edges">{edges}</g><g class="nodes">{nodes}</g></g>')