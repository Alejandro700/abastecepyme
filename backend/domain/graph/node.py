from dataclasses import dataclass

from .errors import InvalidNodeIdError


def validate_node_id(value: object, field_name: str = "id") -> str:
    """Comprueba que el id sea un texto no vacío y sin espacios en los extremos."""

    if not isinstance(value, str):
        raise InvalidNodeIdError(
            f"{field_name} debe ser str, se recibió {type(value).__name__}."
        )
    if not value.strip():
        raise InvalidNodeIdError(f"{field_name} no puede estar vacío.")
    if value != value.strip():
        raise InvalidNodeIdError(
            f"{field_name} no puede tener espacios al inicio o al final: {value!r}."
        )
    return value


@dataclass(frozen=True, slots=True)
class Node:
    """Nodo del grafo, identificado por su id."""

    id: str

    def __post_init__(self) -> None:
        # Valida al construir: no puede existir un Node inválido.
        validate_node_id(self.id, field_name="El id del nodo")

    def __str__(self) -> str:
        return self.id
