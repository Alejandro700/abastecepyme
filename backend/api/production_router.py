"""Endpoints del orden de producción (Feature 3).

Calculan un orden de preparación sobre la red; no modifican nada. Si las
dependencias se contradicen (un ciclo), responden 409 y no devuelven un orden.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from application import CatalogService
from domain.dependency_catalog import Elemento, OrdenProduccion

from .dependencies import get_catalog_service
from .schemas import ElementoResponse, ErrorResponse, EtapaResponse, OrdenResponse

router = APIRouter(prefix="/api", tags=["producción"])

ServicioCatalogo = Annotated[CatalogService, Depends(get_catalog_service)]

ERROR_CICLO = {
    "model": ErrorResponse,
    "description": (
        "Las dependencias forman un ciclo y no hay un orden válido. "
        "`details` trae el ciclo concreto y los elementos bloqueados."
    ),
}

ERRORES_ORDEN_GLOBAL = {status.HTTP_409_CONFLICT: ERROR_CICLO}

ERRORES_ORDEN_ELEMENTO = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "El elemento no existe en el catálogo.",
    },
    status.HTTP_409_CONFLICT: ERROR_CICLO,
}


def _a_respuesta_elemento(elemento: Elemento) -> ElementoResponse:
    return ElementoResponse(id=elemento.id, tipo=elemento.tipo)


def _a_respuesta(orden: OrdenProduccion) -> OrdenResponse:
    total = orden.total_elementos
    etapas = orden.total_etapas

    if total == 0:
        mensaje = "No hay elementos que ordenar."
    elif orden.objetivo is None:
        mensaje = f"Orden de preparación: {total} elementos en {etapas} etapas."
    else:
        mensaje = (
            f"Para producir '{orden.objetivo.id}' hay que preparar {total} "
            f"elementos en {etapas} etapas; '{orden.objetivo.id}' va al final."
        )

    return OrdenResponse(
        objetivo=_a_respuesta_elemento(orden.objetivo) if orden.objetivo else None,
        mensaje=mensaje,
        total_elementos=total,
        total_etapas=etapas,
        etapas=[
            EtapaResponse(
                numero=etapa.numero,
                elementos=[_a_respuesta_elemento(e) for e in etapa.elementos],
            )
            for etapa in orden.etapas
        ],
        secuencia=[_a_respuesta_elemento(e) for e in orden.secuencia],
    )


@router.get(
    "/orden",
    response_model=OrdenResponse,
    summary="Orden de preparación de toda la red",
    responses=ERRORES_ORDEN_GLOBAL,
)
def orden_de_toda_la_red(servicio: ServicioCatalogo) -> OrdenResponse:
    """Devuelve un orden válido de preparación, por etapas.

    Primero va lo que no requiere nada (proveedores). Si las dependencias forman
    un ciclo responde 409 con el ciclo, y nunca un orden falso.
    """
    return _a_respuesta(servicio.consultar_orden())


@router.get(
    "/elementos/{id_elemento}/orden",
    response_model=OrdenResponse,
    summary="Orden de preparación para producir un elemento",
    responses=ERRORES_ORDEN_ELEMENTO,
)
def orden_para_producir(id_elemento: str, servicio: ServicioCatalogo) -> OrdenResponse:
    """Devuelve el orden para producir un elemento, con solo lo que necesita.

    Un ciclo ajeno a esa cadena no lo bloquea.
    """
    return _a_respuesta(servicio.consultar_orden(id_elemento))
