
from enum import Enum

from .errors import TipoElementoInvalidoError


class TipoElemento(str, Enum):


    PRODUCTO = "PRODUCTO"
    INSUMO = "INSUMO"
    PROVEEDOR = "PROVEEDOR"

    @classmethod
    def valores(cls) -> tuple[str, ...]:
        return tuple(tipo.value for tipo in cls)

    @classmethod
    def desde_texto(cls, valor: object) -> "TipoElemento":

        if isinstance(valor, cls):
            return valor
        if not isinstance(valor, str):
            raise TipoElementoInvalidoError(valor, cls.valores())
        try:
            return cls(valor.strip().upper())
        except ValueError:
            # `from None` corta el encadenamiento con el ValueError interno de
            # Enum: al usuario le sirve el mensaje de negocio, no el de stdlib.
            raise TipoElementoInvalidoError(valor, cls.valores()) from None
