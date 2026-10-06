from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Dependencia:
    """Relación dirigida: `origen_id` requiere a `destino_id`."""

    origen_id: str
    destino_id: str

    def frase(self) -> str:
        return f"Para producir/preparar {self.origen_id} necesito {self.destino_id}"

    def __str__(self) -> str:
        return f"{self.origen_id} requiere {self.destino_id}"
