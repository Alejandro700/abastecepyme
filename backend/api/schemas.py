from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.dependency_catalog import SentidoConsulta, TipoElemento

_TIPOS = ", ".join(TipoElemento.valores())


class CrearElementoRequest(BaseModel):
    """Cuerpo para registrar un elemento."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"id": "Silla", "tipo": "PRODUCTO"}}
    )

    id: str = Field(
        ...,
        description="Identificador único del elemento. No distingue mayúsculas.",
        min_length=1,
    )
    tipo: str = Field(..., description=f"Uno de: {_TIPOS}.")


class ElementoResponse(BaseModel):
    """Elemento tal como lo recibe el cliente."""

    id: str
    tipo: TipoElemento


class CrearDependenciaRequest(BaseModel):
    """Cuerpo para registrar que un elemento requiere a otro."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"origen_id": "Silla", "destino_id": "Madera"}
        }
    )

    origen_id: str = Field(
        ..., description="Elemento que REQUIERE al destino.", min_length=1
    )
    destino_id: str = Field(
        ..., description="Elemento REQUERIDO por el origen.", min_length=1
    )


class DependenciaResponse(BaseModel):
    """Dependencia con su frase en lenguaje natural."""

    origen_id: str
    destino_id: str
    frase: str = Field(
        ...,
        description=(
            "La relación en lenguaje natural. Hace la dirección evidente "
            "para quien consume la API sin leer la documentación."
        ),
    )


class RedResponse(BaseModel):
    """Elementos y dependencias juntos, con sus totales."""

    elementos: list[ElementoResponse]
    dependencias: list[DependenciaResponse]
    total_elementos: int
    total_dependencias: int


class ElementoAlcanzadoResponse(BaseModel):
    """Elemento alcanzado por una consulta, con la cadena que lo explica."""

    id: str
    tipo: TipoElemento
    nivel: int = Field(
        ...,
        description="1 si la relación es directa, 2 si pasa por otro elemento, etc.",
    )
    cadena: list[str] = Field(
        ...,
        description=(
            "Camino más corto, en el sentido de las flechas: cada elemento "
            "requiere al siguiente."
        ),
    )
    explicacion: str = Field(..., description="La cadena en lenguaje natural.")


class AlcanceResponse(BaseModel):
    """Resultado de consultar el impacto o los requisitos de un elemento."""

    consultado: ElementoResponse
    sentido: SentidoConsulta
    estado: Literal["CON_IMPACTO", "SIN_IMPACTO", "CON_REQUISITOS", "SIN_REQUISITOS"] = (
        Field(
            ...,
            description=(
                "Distingue un elemento que afecta una cadena (o necesita una) "
                "de uno que no tiene dependencias en ese sentido."
            ),
        )
    )
    mensaje: str
    total: int
    alcanzados: list[ElementoAlcanzadoResponse] = Field(
        ..., description="En orden de cercanía: primero los directos."
    )


class ErrorResponse(BaseModel):
    """Formato único de error de la API."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "ELEMENTO_DUPLICADO",
                "message": "Ya existe un elemento con el identificador 'Silla'.",
                "details": {"id_solicitado": "silla", "id_existente": "Silla"},
            }
        }
    )

    error_code: str = Field(
        ..., description="Código estable, pensado para que el cliente lo compare."
    )
    message: str = Field(..., description="Mensaje legible para la persona usuaria.")
    details: dict = Field(
        default_factory=dict,
        description="Datos del caso concreto. Puede venir vacío.",
    )
