

from fastapi import FastAPI, Request, status


HTTP_422 = 422
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from domain.dependency_catalog import (
    AutodependenciaError,
    CatalogoError,
    DependenciaDuplicadaError,
    ElementoDuplicadoError,
    ElementoNoEncontradoError,
    IdElementoInvalidoError,
    TipoElementoInvalidoError,
)


MAPEO_ERRORES: tuple[tuple[type[CatalogoError], int, str], ...] = (
    (ElementoNoEncontradoError, status.HTTP_404_NOT_FOUND, "ELEMENTO_NO_ENCONTRADO"),
    (ElementoDuplicadoError, status.HTTP_409_CONFLICT, "ELEMENTO_DUPLICADO"),
    (DependenciaDuplicadaError, status.HTTP_409_CONFLICT, "DEPENDENCIA_DUPLICADA"),
    (
        AutodependenciaError,
        HTTP_422,
        "AUTODEPENDENCIA",
    ),
    (
        TipoElementoInvalidoError,
        HTTP_422,
        "TIPO_INVALIDO",
    ),
    (
        IdElementoInvalidoError,
        HTTP_422,
        "ID_INVALIDO",
    ),
)


def _detalles(error: CatalogoError) -> dict:

    return {
        clave: valor
        for clave, valor in vars(error).items()
        if not clave.startswith("_")
    }


def _respuesta(codigo_http: int, error_code: str, mensaje: str, detalles: dict):
    return JSONResponse(
        status_code=codigo_http,
        content={
            "error_code": error_code,
            "message": mensaje,
            "details": detalles,
        },
    )


async def manejar_error_catalogo(_: Request, error: CatalogoError) -> JSONResponse:
    for tipo_error, codigo_http, error_code in MAPEO_ERRORES:
        if isinstance(error, tipo_error):
            return _respuesta(codigo_http, error_code, str(error), _detalles(error))


    return _respuesta(
        HTTP_422,
        "ERROR_DE_CATALOGO",
        str(error),
        _detalles(error),
    )


async def manejar_error_de_formato(
    _: Request, error: RequestValidationError
) -> JSONResponse:

    return _respuesta(
        HTTP_422,
        "CUERPO_INVALIDO",
        "El cuerpo de la petición no tiene el formato esperado.",
        {"errores": error.errors()},
    )


def registrar_manejadores(app: FastAPI) -> None:

    app.add_exception_handler(CatalogoError, manejar_error_catalogo)
    app.add_exception_handler(RequestValidationError, manejar_error_de_formato)
