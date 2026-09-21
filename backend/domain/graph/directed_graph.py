

from .edge import Edge
from .errors import DuplicateEdgeError, DuplicateNodeError, NodeNotFoundError
from .node import Node, validate_node_id


class DirectedGraph:

    def __init__(self) -> None:
        # dict preserva el orden de inserción (garantizado desde Python 3.7),
        # así que listar nodos devuelve siempre el mismo orden: útil para que
        # la API y los tests sean deterministas.
        self._nodes: dict[str, Node] = {}
        self._successors: dict[str, set[str]] = {}
        self._predecessors: dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Nodos
    # ------------------------------------------------------------------

    def add_node(self, node: Node) -> Node:

        if not isinstance(node, Node):
            raise TypeError(
                f"add_node espera un Node, se recibió {type(node).__name__}."
            )
        if node.id in self._nodes:
            raise DuplicateNodeError(node.id)

        self._nodes[node.id] = node
        self._successors[node.id] = set()
        self._predecessors[node.id] = set()
        return node

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def get_node(self, node_id: str) -> Node:
        self._require_node(node_id)
        return self._nodes[node_id]

    def nodes(self) -> tuple[Node, ...]:
        return tuple(self._nodes.values())

    def node_count(self) -> int:
        return len(self._nodes)

    # ------------------------------------------------------------------
    # Aristas
    # ------------------------------------------------------------------

    def add_edge(self, source_id: str, target_id: str) -> Edge:

        validate_node_id(source_id, field_name="El id origen de la arista")
        validate_node_id(target_id, field_name="El id destino de la arista")
        self._require_node(source_id)
        self._require_node(target_id)

        if target_id in self._successors[source_id]:
            raise DuplicateEdgeError(source_id, target_id)

        self._successors[source_id].add(target_id)
        self._predecessors[target_id].add(source_id)
        return Edge(source_id=source_id, target_id=target_id)

    def has_edge(self, source_id: str, target_id: str) -> bool:

        if source_id not in self._successors:
            return False
        return target_id in self._successors[source_id]

    def edges(self) -> tuple[Edge, ...]:

        result: list[Edge] = []
        for source_id in self._nodes:
            for target_id in sorted(self._successors[source_id]):
                result.append(Edge(source_id=source_id, target_id=target_id))
        return tuple(result)

    def edge_count(self) -> int:
        return sum(len(targets) for targets in self._successors.values())

    # ------------------------------------------------------------------
    # Vecindad
    # ------------------------------------------------------------------

    def successors(self, node_id: str) -> frozenset[str]:

        self._require_node(node_id)
        return frozenset(self._successors[node_id])

    def predecessors(self, node_id: str) -> frozenset[str]:

        self._require_node(node_id)
        return frozenset(self._predecessors[node_id])

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _require_node(self, node_id: str) -> None:

        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)

    def __repr__(self) -> str:
        return (
            f"DirectedGraph(nodes={self.node_count()}, edges={self.edge_count()})"
        )
