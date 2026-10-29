"""Endpoints del análisis de impacto (Feature 2).

Recorren la red que construye el catálogo; no modifican nada.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from application import CatalogService
from domain.dependency_catalog import Alcance, SentidoConsulta

from .dependencies import get_catalog_service
from .schemas import (
    AlcanceResponse,
    ElementoAlcanzadoResponse,
    ElementoResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/api/elementos", tags=["impacto"])

ServicioCatalogo = Annotated[CatalogService, Depends(get_catalog_service)]

ERROR_NO_EXISTE = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "El elemento no existe en el catálogo.",
    },
}


def _plural(total: int) -> str:
    return "elemento" if total == 1 else "elementos"


def _a_respuesta(alcance: Alcance) -> AlcanceResponse:
    id_elemento = alcance.consultado.id
    total = alcance.total

    if alcance.sentido is SentidoConsulta.IMPACTO:
        if total:
            verbo = "se afecta" if total == 1 else "se afectan"
            estado = "CON_IMPACTO"
            mensaje = (
                f"Si '{id_elemento}' deja de estar disponible, {verbo} {total} "
                f"{_plural(total)}."
            )
        else:
            estado = "SIN_IMPACTO"
            mensaje = (
                f"Nadie requiere a '{id_elemento}': su falta no afecta a "
                f"ningún otro elemento."
            )
    else:
        if total:
            estado = "CON_REQUISITOS"
            mensaje = (
                f"'{id_elemento}' necesita {total} {_plural(total)}, directa "
                f"o indirectamente."
            )
        else:
            estado = "SIN_REQUISITOS"
            mensaje = f"'{id_elemento}' no requiere ningún otro elemento."

    return AlcanceResponse(
        consultado=ElementoResponse(id=id_elemento, tipo=alcance.consultado.tipo),
        sentido=alcance.sentido,
        estado=estado,
        mensaje=mensaje,
        total=total,
        alcanzados=[
            ElementoAlcanzadoResponse(
                id=alcanzado.elemento.id,
                tipo=alcanzado.elemento.tipo,
                nivel=alcanzado.nivel,
                cadena=list(alcanzado.cadena),
                explicacion=alcanzado.explicacion(),
            )
            for alcanzado in alcance.alcanzados
        ],
    )


@router.get(
    "/{id_elemento}/impacto",
    response_model=AlcanceResponse,
    summary="Qué se afecta si un elemento deja de estar disponible",
    responses=ERROR_NO_EXISTE,
)
def consultar_impacto(id_elemento: str, servicio: ServicioCatalogo) -> AlcanceResponse:
    """Devuelve los elementos que requieren, directa o indirectamente, al consultado.

    Sirve para simular la falta de un proveedor o insumo. Un elemento que nadie
    requiere responde 200 con la lista vacía; uno que no existe responde 404.
    """
    return _a_respuesta(servicio.consultar_impacto(id_elemento))


@router.get(
    "/{id_elemento}/requisitos",
    response_model=AlcanceResponse,
    summary="Qué necesita un elemento para producirse",
    responses=ERROR_NO_EXISTE,
)
def consultar_requisitos(
    id_elemento: str, servicio: ServicioCatalogo
) -> AlcanceResponse:
    """Devuelve los elementos que el consultado necesita, directa o indirectamente."""
    return _a_respuesta(servicio.consultar_requisitos(id_elemento))
