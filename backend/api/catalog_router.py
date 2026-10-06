"""Endpoints del catálogo de dependencias (Feature 1).

El router solo traduce HTTP a casos de uso; las reglas viven en `domain/`
y los errores se convierten en `api/errors.py`.
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

ServicioCatalogo = Annotated[CatalogService, Depends(get_catalog_service)]

# Respuestas de error que se muestran en /docs.
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
    """Convierte la entidad de dominio en su representación HTTP."""
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
    """Da de alta un elemento del catálogo y devuelve 201."""
    return _a_respuesta_elemento(servicio.crear_elemento(cuerpo.id, cuerpo.tipo))


@router.get(
    "/elementos",
    response_model=list[ElementoResponse],
    summary="Listar todos los elementos",
)


def listar_elementos(servicio: ServicioCatalogo) -> list[ElementoResponse]:
    """Lista los elementos en orden de alta. Un catálogo vacío devuelve `[]`."""
    return [_a_respuesta_elemento(e) for e in servicio.listar_elementos()]


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


@router.get(
    "/red",
    response_model=RedResponse,
    summary="Obtener la red completa de dependencias",
)


def obtener_red(servicio: ServicioCatalogo) -> RedResponse:
    """Devuelve elementos y dependencias juntos, listos para dibujar la red."""
    return _a_respuesta_red(servicio.obtener_red())
