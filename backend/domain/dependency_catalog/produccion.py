from dataclasses import dataclass

from .elemento import Elemento


@dataclass(frozen=True, slots=True)
class EtapaProduccion:
    """Elementos que se pueden preparar a la vez: no dependen entre sí."""

    numero: int
    elementos: tuple[Elemento, ...]


@dataclass(frozen=True, slots=True)
class OrdenProduccion:
    """Orden válido de preparación: primero lo que no requiere nada."""

    objetivo: Elemento | None
    etapas: tuple[EtapaProduccion, ...]

    @property
    def secuencia(self) -> tuple[Elemento, ...]:
        return tuple(e for etapa in self.etapas for e in etapa.elementos)

    @property
    def total_elementos(self) -> int:
        return len(self.secuencia)

    @property
    def total_etapas(self) -> int:
        return len(self.etapas)
