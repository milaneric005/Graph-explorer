from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Optional, Union

AttributeValue = Union[int, float, str, date]
_ALLOWED_TYPES = (int, float, str, date)


class GraphError(Exception):
    """Raised when an operation on the graph is invalid."""


class _Attributed:
    """Base for objects that carry typed attributes (nodes and edges).

    Values keep their real Python type (int, float, str, date); they are
    never stored as plain strings.
    """

    def _init_attributes(self, attributes: Optional[Dict[str, AttributeValue]]) -> None:
        self.attributes: Dict[str, AttributeValue] = {}
        for name, value in (attributes or {}).items():
            self.set_attribute(name, value)

    def set_attribute(self, name: str, value: AttributeValue) -> None:
        """Set an attribute. Raises TypeError for unsupported value types."""
        if isinstance(value, bool) or not isinstance(value, _ALLOWED_TYPES):
            raise TypeError(
                f"Unsupported type for attribute '{name}': {type(value).__name__} "
                f"(allowed: int, float, str, date)"
            )
        self.attributes[name] = value

    def get_attribute(self, name: str, default: Optional[AttributeValue] = None) -> Optional[AttributeValue]:
        return self.attributes.get(name, default)

    def remove_attribute(self, name: str) -> None:
        self.attributes.pop(name, None)


class Node(_Attributed):
    """A graph node identified by a unique node_id."""

    def __init__(self, node_id: str, attributes: Optional[Dict[str, AttributeValue]] = None):
        self.node_id = node_id
        self._init_attributes(attributes)

    def __repr__(self) -> str:
        return f"Node(node_id={self.node_id!r}, attributes={self.attributes!r})"


class Edge(_Attributed):
    """An edge identified by a unique edge_id, going from source to target.

    Whether the edge is directed is decided by the Graph that contains it.
    """

    def __init__(self, edge_id: str, source: Node, target: Node,
                 attributes: Optional[Dict[str, AttributeValue]] = None):
        self.edge_id = edge_id
        self.source = source
        self.target = target
        self._init_attributes(attributes)

    def __repr__(self) -> str:
        return (f"Edge(edge_id={self.edge_id!r}, {self.source.node_id!r} -> "
                f"{self.target.node_id!r}, attributes={self.attributes!r})")


class Graph:
    """Generic graph: directed or undirected, cyclic or acyclic, connected or not.

    Self-loops and parallel edges (several edges between the same nodes,
    A->B and B->A) are allowed.

    get_node/get_edge return None when the id does not exist; operations that
    change the graph (add_*, remove_*) raise GraphError when they are invalid.
    """

    def __init__(self, directed: bool = True):
        self._directed = directed
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}

    @property
    def directed(self) -> bool:
        return self._directed

    @property
    def nodes(self) -> List[Node]:
        return list(self._nodes.values())

    @property
    def edges(self) -> List[Edge]:
        return list(self._edges.values())

    # ---- nodes ----
    def add_node(self, node: Node) -> None:
        if node.node_id in self._nodes:
            raise GraphError(f"Node '{node.node_id}' already exists")
        self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def remove_node(self, node_id: str) -> None:
        """Remove a node. Raises GraphError if it does not exist or still has edges."""
        if node_id not in self._nodes:
            raise GraphError(f"Node '{node_id}' does not exist")
        if self.edges_of(node_id):
            raise GraphError(f"Node '{node_id}' is connected to edges; remove them first")
        del self._nodes[node_id]

    # ---- edges ----
    def add_edge(self, edge: Edge) -> None:
        """Add an edge. Raises GraphError if the id is taken or an endpoint is not in the graph."""
        if edge.edge_id in self._edges:
            raise GraphError(f"Edge '{edge.edge_id}' already exists")
        for endpoint in (edge.source, edge.target):
            if endpoint.node_id not in self._nodes:
                raise GraphError(
                    f"Edge '{edge.edge_id}' references node '{endpoint.node_id}' "
                    f"which is not in the graph"
                )
        self._edges[edge.edge_id] = edge

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        return self._edges.get(edge_id)

    def remove_edge(self, edge_id: str) -> None:
        if edge_id not in self._edges:
            raise GraphError(f"Edge '{edge_id}' does not exist")
        del self._edges[edge_id]

    def edges_of(self, node_id: str) -> List[Edge]:
        """All edges that start or end in the given node."""
        return [e for e in self._edges.values()
                if e.source.node_id == node_id or e.target.node_id == node_id]

    # ---- queries ----
    def neighbors(self, node_id: str) -> List[Node]:
        """Neighbors of a node, without duplicates.

        Directed graph: only nodes reachable through outgoing edges.
        Undirected graph: nodes on the other end of every incident edge.
        Raises GraphError if the node does not exist.
        """
        if node_id not in self._nodes:
            raise GraphError(f"Node '{node_id}' does not exist")
        result: Dict[str, Node] = {}
        for e in self._edges.values():
            if e.source.node_id == node_id:
                result[e.target.node_id] = self._nodes[e.target.node_id]
            elif not self._directed and e.target.node_id == node_id:
                result[e.source.node_id] = self._nodes[e.source.node_id]
        return list(result.values())

    def subgraph(self, node_ids: Iterable[str]) -> "Graph":
        """New graph with the given nodes and every edge between them.

        Unknown ids are ignored. Node and edge objects are shared with this graph.
        """
        wanted = set(node_ids)
        result = Graph(self._directed)
        for node in self._nodes.values():
            if node.node_id in wanted:
                result.add_node(node)
        for edge in self._edges.values():
            if edge.source.node_id in wanted and edge.target.node_id in wanted:
                result.add_edge(edge)
        return result

    def clear(self) -> None:
        """Remove all nodes and edges."""
        self._nodes.clear()
        self._edges.clear()