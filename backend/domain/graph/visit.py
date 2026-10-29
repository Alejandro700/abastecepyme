from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Visit:
    """Nodo alcanzado en un recorrido: a qué distancia y por qué camino."""

    node_id: str
    depth: int
    path: tuple[str, ...]
