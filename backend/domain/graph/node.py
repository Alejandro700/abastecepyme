

from dataclasses import dataclass

from .errors import InvalidNodeIdError


def validate_node_id(value: object, field_name: str = "id") -> str:

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


    id: str

    def __post_init__(self) -> None:
        # Se ejecuta apenas termina de construirse la instancia. Valida el id
        # aquí para que sea imposible que exista un Node inválido en memoria.
        validate_node_id(self.id, field_name="El id del nodo")

    def __str__(self) -> str:
        return self.id
