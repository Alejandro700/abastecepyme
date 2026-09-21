"""Endpoints del Feature 1: catálogo de dependencias.

El router solo traduce: convierte una petición HTTP en una llamada al caso de
uso y el resultado en JSON. No valida reglas ni captura errores de negocio;
de eso se encargan `domain/` y `api/errors.py` respectivamente.

Que los endpoints sean de tres líneas no es pereza: es la señal de que la
lógica está donde corresponde. Este archivo se podría reescribir para otro
framework web sin tocar nada más del sistema.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from application import CatalogService, RedDependencias
from domain.dependency_catalog import Dependencia, Elemento

from .dependencies import get_catalog_service
from .errors import HTTP_422
from .schemas import (
    CrearDependenciaRequest,
    CrearElementoRequest,
    DependenciaResponse,
    ElementoResponse,
    ErrorResponse,
    RedResponse,
)

router = APIRouter(prefix="/api", tags=["catálogo"])

# Alias para no repetir la firma completa en cada endpoint.
ServicioCatalogo = Annotated[CatalogService, Depends(get_catalog_service)]

# Respuestas de error documentadas en OpenAPI. Sin esto, /docs solo mostraría
# el caso feliz y quien consuma la API no sabría qué esperar cuando falle.
ERRORES_ALTA_ELEMENTO = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "Ya existe un elemento con ese identificador.",
    },
    HTTP_422: {
        "model": ErrorResponse,
        "description": "Identificador o tipo mal formados.",
    },
}

ERRORES_ALTA_DEPENDENCIA = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "Alguno de los dos elementos no existe.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "La dependencia ya estaba registrada.",
    },
    HTTP_422: {
        "model": ErrorResponse,
        "description": "Datos mal formados o autodependencia.",
    },
}


def _a_respuesta_elemento(elemento: Elemento) -> ElementoResponse:
    """Convierte la entidad de dominio en su representación HTTP.

    El mapeo es explícito y no automático: así el dominio puede sumar campos
    internos sin que se filtren a la API por accidente.
    """
    return ElementoResponse(id=elemento.id, tipo=elemento.tipo)


def _a_respuesta_dependencia(dependencia: Dependencia) -> DependenciaResponse:
    return DependenciaResponse(
        origen_id=dependencia.origen_id,
        destino_id=dependencia.destino_id,
        frase=dependencia.frase(),
    )


def _a_respuesta_red(red: RedDependencias) -> RedResponse:
    return RedResponse(
        elementos=[_a_respuesta_elemento(e) for e in red.elementos],
        dependencias=[_a_respuesta_dependencia(d) for d in red.dependencias],
        total_elementos=red.total_elementos,
        total_dependencias=red.total_dependencias,
    )


# ----------------------------------------------------------------------
# Elementos
# ----------------------------------------------------------------------


@router.post(
    "/elementos",
    response_model=ElementoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un producto, insumo o proveedor",
    responses=ERRORES_ALTA_ELEMENTO,
)
def crear_elemento(
    cuerpo: CrearElementoRequest, servicio: ServicioCatalogo
) -> ElementoResponse:
    """Da de alta un elemento del catálogo.

    Devuelve 201 y no 200: se creó un recurso nuevo.
    """
    return _a_respuesta_elemento(servicio.crear_elemento(cuerpo.id, cuerpo.tipo))


@router.get(
    "/elementos",
    response_model=list[ElementoResponse],
    summary="Listar todos los elementos",
)
def listar_elementos(servicio: ServicioCatalogo) -> list[ElementoResponse]:
    """Lista los elementos en orden de alta.

    Un catálogo vacío devuelve 200 con `[]`, no 404: "no hay nada cargado" es
    una respuesta correcta, no un recurso inexistente.
    """
    return [_a_respuesta_elemento(e) for e in servicio.listar_elementos()]


# ----------------------------------------------------------------------
# Dependencias
# ----------------------------------------------------------------------


@router.post(
    "/dependencias",
    response_model=DependenciaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar que un elemento requiere a otro",
    responses=ERRORES_ALTA_DEPENDENCIA,
)
def crear_dependencia(
    cuerpo: CrearDependenciaRequest, servicio: ServicioCatalogo
) -> DependenciaResponse:
    """Registra la relación `origen_id` REQUIERE `destino_id`."""
    return _a_respuesta_dependencia(
        servicio.crear_dependencia(cuerpo.origen_id, cuerpo.destino_id)
    )


@router.get(
    "/dependencias",
    response_model=list[DependenciaResponse],
    summary="Listar todas las dependencias",
)
def listar_dependencias(servicio: ServicioCatalogo) -> list[DependenciaResponse]:
    """Lista las dependencias en orden estable."""
    return [_a_respuesta_dependencia(d) for d in servicio.listar_dependencias()]


# ----------------------------------------------------------------------
# Red completa
# ----------------------------------------------------------------------


@router.get(
    "/red",
    response_model=RedResponse,
    summary="Obtener la red completa de dependencias",
)
def obtener_red(servicio: ServicioCatalogo) -> RedResponse:
    """Devuelve elementos y dependencias juntos, listos para dibujar.

    Un solo endpoint en vez de dos llamadas encadenadas: garantiza que toda
    dependencia apunte a elementos presentes en la misma respuesta.
    """
    return _a_respuesta_red(servicio.obtener_red())
