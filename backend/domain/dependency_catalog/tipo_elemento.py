from enum import Enum

from .errors import TipoElementoInvalidoError


class TipoElemento(str, Enum):
    """Clases de elemento que admite el catálogo."""

    PRODUCTO = "PRODUCTO"
    INSUMO = "INSUMO"
    PROVEEDOR = "PROVEEDOR"

    @classmethod
    def valores(cls) -> tuple[str, ...]:
        return tuple(tipo.value for tipo in cls)

    @classmethod
    def desde_texto(cls, valor: object) -> "TipoElemento":
        """Convierte un texto en tipo, tolerando mayúsculas y espacios."""

        if isinstance(valor, cls):
            return valor
        if not isinstance(valor, str):
            raise TipoElementoInvalidoError(valor, cls.valores())
        try:
            return cls(valor.strip().upper())
        except ValueError:
            # `from None` oculta el ValueError interno del Enum.
            raise TipoElementoInvalidoError(valor, cls.valores()) from None
