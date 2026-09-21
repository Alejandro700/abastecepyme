
from dataclasses import dataclass

from .errors import IdElementoInvalidoError
from .tipo_elemento import TipoElemento

LONGITUD_MAXIMA_ID = 120


def normalizar_id(valor: object) -> str:

    if not isinstance(valor, str):
        raise IdElementoInvalidoError(
            f"El identificador debe ser texto, se recibió "
            f"{type(valor).__name__}."
        )
    limpio = valor.strip()
    if not limpio:
        raise IdElementoInvalidoError(
            "El identificador no puede estar vacío."
        )
    if len(limpio) > LONGITUD_MAXIMA_ID:
        raise IdElementoInvalidoError(
            f"El identificador no puede superar {LONGITUD_MAXIMA_ID} "
            f"caracteres (recibidos: {len(limpio)})."
        )
    return limpio


def clave_de(id_elemento: str) -> str:

    return id_elemento.casefold()


@dataclass(frozen=True, slots=True)
class Elemento:


    id: str
    tipo: TipoElemento

    def __post_init__(self) -> None:

        if not isinstance(self.id, str) or self.id != self.id.strip() or not self.id:
            raise IdElementoInvalidoError(
                f"Identificador inválido para Elemento: {self.id!r}. "
                f"Usá Elemento.crear() para normalizar la entrada del usuario."
            )
        if not isinstance(self.tipo, TipoElemento):
            raise IdElementoInvalidoError(
                f"El tipo debe ser un TipoElemento, se recibió "
                f"{type(self.tipo).__name__}."
            )

    @classmethod
    def crear(cls, id_elemento: object, tipo: object) -> "Elemento":
        return cls(
            id=normalizar_id(id_elemento),
            tipo=TipoElemento.desde_texto(tipo),
        )

    @property
    def clave(self) -> str:
        return clave_de(self.id)

    def __str__(self) -> str:
        return f"{self.tipo.value}:{self.id}"
