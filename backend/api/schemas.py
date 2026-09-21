

from pydantic import BaseModel, ConfigDict, Field

from domain.dependency_catalog import TipoElemento

_TIPOS = ", ".join(TipoElemento.valores())


class CrearElementoRequest(BaseModel):

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

    id: str
    tipo: TipoElemento


class CrearDependenciaRequest(BaseModel):


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


    elementos: list[ElementoResponse]
    dependencias: list[DependenciaResponse]
    total_elementos: int
    total_dependencias: int


class ErrorResponse(BaseModel):


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
