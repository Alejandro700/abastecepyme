

from dataclasses import dataclass

from .node import validate_node_id


@dataclass(frozen=True, slots=True)
class Edge:


    source_id: str
    target_id: str

    def __post_init__(self) -> None:
        validate_node_id(self.source_id, field_name="El id origen de la arista")
        validate_node_id(self.target_id, field_name="El id destino de la arista")

    def __str__(self) -> str:
        return f"{self.source_id} -> {self.target_id}"
