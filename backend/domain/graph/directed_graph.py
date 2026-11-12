from collections import deque
from collections.abc import Iterable

from .edge import Edge
from .errors import (
    CycleError,
    DuplicateEdgeError,
    DuplicateNodeError,
    EdgeNotFoundError,
    NodeNotFoundError,
)
from .node import Node, validate_node_id
from .visit import Visit


class DirectedGraph:
    """Grafo dirigido de nodos con identificador único."""

    def __init__(self) -> None:
        # dict conserva el orden de inserción: los listados son deterministas.
        self._nodes: dict[str, Node] = {}
        self._successors: dict[str, set[str]] = {}
        self._predecessors: dict[str, set[str]] = {}

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

    def remove_edge(self, source_id: str, target_id: str) -> None:
        if not self.has_edge(source_id, target_id):
            raise EdgeNotFoundError(source_id, target_id)
        self._successors[source_id].discard(target_id)
        self._predecessors[target_id].discard(source_id)

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

    def successors(self, node_id: str) -> frozenset[str]:
        self._require_node(node_id)
        return frozenset(self._successors[node_id])

    def predecessors(self, node_id: str) -> frozenset[str]:
        self._require_node(node_id)
        return frozenset(self._predecessors[node_id])

    def descendants(self, node_id: str) -> tuple[Visit, ...]:
        """Todo lo que `node_id` alcanza siguiendo las flechas, directa o indirectamente."""
        return self._breadth_first(node_id, self._successors)

    def ancestors(self, node_id: str) -> tuple[Visit, ...]:
        """Todo lo que alcanza a `node_id` siguiendo las flechas, directa o indirectamente."""
        return self._breadth_first(node_id, self._predecessors)

    def build_layers(
        self, only: Iterable[str] | None = None
    ) -> tuple[tuple[str, ...], ...]:
        """Capas de construcción: cada nodo aparece después de todos a los que apunta.

        La primera capa son los nodos sin salidas pendientes. Los de una misma
        capa no dependen entre sí. Con `only` se considera solo ese subconjunto.
        Lanza CycleError si hay un ciclo, porque entonces no existe un orden válido.
        """
        scope = set(self._nodes) if only is None else set(only)
        for node_id in scope:
            self._require_node(node_id)

        # Salidas pendientes de cada nodo, contando solo las que están en el alcance.
        pending = {node_id: len(self._successors[node_id] & scope) for node_id in scope}

        layers: list[tuple[str, ...]] = []
        ready = sorted(node_id for node_id, count in pending.items() if count == 0)
        placed = 0

        while ready:
            layers.append(tuple(ready))
            placed += len(ready)
            next_ready: list[str] = []
            for node_id in ready:
                for dependent_id in self._predecessors[node_id] & scope:
                    pending[dependent_id] -= 1
                    if pending[dependent_id] == 0:
                        next_ready.append(dependent_id)
            ready = sorted(next_ready)

        if placed < len(scope):
            blocked = tuple(sorted(n for n, count in pending.items() if count > 0))
            raise CycleError(self._cycle_among(set(blocked)), blocked)

        return tuple(layers)

    def _cycle_among(self, blocked: set[str]) -> tuple[str, ...]:
        """Un ciclo concreto dentro de los nodos que no se pudieron ordenar.

        Cada nodo bloqueado tiene al menos una salida también bloqueada, así que
        seguir esas salidas termina por repetir un nodo: ahí se cierra el ciclo.
        """
        current = min(blocked)
        path = [current]
        position = {current: 0}

        while True:
            current = min(self._successors[current] & blocked)
            if current in position:
                return tuple(path[position[current] :]) + (current,)
            position[current] = len(path)
            path.append(current)

    def _breadth_first(
        self, start_id: str, neighbors: dict[str, set[str]]
    ) -> tuple[Visit, ...]:
        """Recorrido en anchura: cada nodo se visita una vez, por su camino más corto."""
        self._require_node(start_id)

        visited = {start_id}
        queue = deque([Visit(node_id=start_id, depth=0, path=(start_id,))])
        result: list[Visit] = []

        while queue:
            current = queue.popleft()
            # Vecinos ordenados: el resultado es siempre el mismo.
            for neighbor_id in sorted(neighbors[current.node_id]):
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                visit = Visit(
                    node_id=neighbor_id,
                    depth=current.depth + 1,
                    path=current.path + (neighbor_id,),
                )
                result.append(visit)
                queue.append(visit)

        return tuple(result)

    def _require_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)

    def __repr__(self) -> str:
        return (
            f"DirectedGraph(nodes={self.node_count()}, edges={self.edge_count()})"
        )
