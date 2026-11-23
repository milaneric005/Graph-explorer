from graph_api import Graph, Node


def _node_matches(node: Node, query: str) -> bool:
    """Da li naziv ili vrednost nekog atributa čvora sadrži upit (bez obzira na velika/mala slova)."""
    for name, value in node.attributes.items():
        if query in name.lower() or query in str(value).lower():
            return True
    return False


def search_graph(graph: Graph, query: str) -> Graph:
   
    normalized = (query or "").strip().lower()
    if not normalized:
        return graph.subgraph(node.node_id for node in graph.nodes)

    matching_ids = [node.node_id for node in graph.nodes if _node_matches(node, normalized)]
    return graph.subgraph(matching_ids)