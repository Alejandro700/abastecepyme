


class GraphError(Exception):
    """Error base del paquete de grafo. Permite capturar todo con un solo except."""


class InvalidNodeIdError(GraphError):
    """El identificador de un nodo no cumple el formato mínimo exigido."""


class NodeNotFoundError(GraphError):

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"El nodo '{node_id}' no existe en el grafo.")


class DuplicateNodeError(GraphError):

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"El nodo '{node_id}' ya existe en el grafo.")


class DuplicateEdgeError(GraphError):

    def __init__(self, source_id: str, target_id: str) -> None:
        self.source_id = source_id
        self.target_id = target_id
        super().__init__(
            f"La arista '{source_id}' -> '{target_id}' ya existe en el grafo."
        )
