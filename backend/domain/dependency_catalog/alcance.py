from dataclasses import dataclass
from enum import Enum

from .cadena import describir_cadena
from .elemento import Elemento


class SentidoConsulta(str, Enum):
    """Hacia dónde se recorre la red a partir de un elemento."""

    IMPACTO = "IMPACTO"
    REQUISITOS = "REQUISITOS"


@dataclass(frozen=True, slots=True)
class ElementoAlcanzado:
    """Elemento alcanzado por una consulta, con la cadena que lo explica."""

    elemento: Elemento
    nivel: int
    cadena: tuple[str, ...]

    def explicacion(self) -> str:
        """La cadena en lenguaje natural: 'Silla requiere Madera, que requiere ...'."""
        return describir_cadena(self.cadena)


@dataclass(frozen=True, slots=True)
class Alcance:
    """Resultado de consultar el impacto o los requisitos de un elemento."""

    consultado: Elemento
    sentido: SentidoConsulta
    alcanzados: tuple[ElementoAlcanzado, ...]

    @property
    def total(self) -> int:
        return len(self.alcanzados)
