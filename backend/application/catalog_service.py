

from dataclasses import dataclass

from domain.dependency_catalog import (
    CatalogRepository,
    Dependencia,
    Elemento,
)


@dataclass(frozen=True, slots=True)
class RedDependencias:


    elementos: tuple[Elemento, ...]
    dependencias: tuple[Dependencia, ...]

    @property
    def total_elementos(self) -> int:
        return len(self.elementos)

    @property
    def total_dependencias(self) -> int:
        return len(self.dependencias)


class CatalogService:

    def __init__(self, repositorio: CatalogRepository) -> None:

        if not isinstance(repositorio, CatalogRepository):
            raise TypeError(
                f"Se esperaba un CatalogRepository, se recibió "
                f"{type(repositorio).__name__}."
            )
        self._repositorio = repositorio

    # ------------------------------------------------------------------
    # Casos de uso de escritura
    # ------------------------------------------------------------------

    def crear_elemento(self, id_elemento: object, tipo: object) -> Elemento:

        catalogo = self._repositorio.obtener()
        elemento = catalogo.registrar_elemento(id_elemento, tipo)

        self._repositorio.guardar(catalogo)
        return elemento

    def crear_dependencia(
        self, origen_id: object, destino_id: object
    ) -> Dependencia:

        catalogo = self._repositorio.obtener()
        dependencia = catalogo.registrar_dependencia(origen_id, destino_id)
        self._repositorio.guardar(catalogo)
        return dependencia

    # ------------------------------------------------------------------
    # Casos de uso de lectura
    # ------------------------------------------------------------------

    def listar_elementos(self) -> tuple[Elemento, ...]:
        return self._repositorio.obtener().listar_elementos()

    def obtener_elemento(self, id_elemento: object) -> Elemento:
        return self._repositorio.obtener().obtener_elemento(id_elemento)

    def listar_dependencias(self) -> tuple[Dependencia, ...]:
        return self._repositorio.obtener().listar_dependencias()

    def obtener_red(self) -> RedDependencias:

        catalogo = self._repositorio.obtener()
        return RedDependencias(
            elementos=catalogo.listar_elementos(),
            dependencias=catalogo.listar_dependencias(),
        )
