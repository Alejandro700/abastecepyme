from dataclasses import dataclass

from domain.dependency_catalog import (
    Alcance,
    CatalogRepository,
    Dependencia,
    DependencyCatalog,
    Elemento,
    OrdenProduccion,
)


@dataclass(frozen=True, slots=True)
class RedDependencias:
    """Elementos y dependencias del catálogo, juntos."""

    elementos: tuple[Elemento, ...]
    dependencias: tuple[Dependencia, ...]

    @property
    def total_elementos(self) -> int:
        return len(self.elementos)

    @property
    def total_dependencias(self) -> int:
        return len(self.dependencias)


class CatalogService:
    """Casos de uso del catálogo de dependencias."""

    def __init__(self, repositorio: CatalogRepository) -> None:
        if not isinstance(repositorio, CatalogRepository):
            raise TypeError(
                f"Se esperaba un CatalogRepository, se recibió "
                f"{type(repositorio).__name__}."
            )
        self._repositorio = repositorio

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

    def eliminar_dependencia(self, origen_id: object, destino_id: object) -> None:
        catalogo = self._repositorio.obtener()
        catalogo.eliminar_dependencia(origen_id, destino_id)
        self._repositorio.guardar(catalogo)

    def vaciar(self) -> None:
        """Borra todos los elementos y dependencias."""
        self._repositorio.guardar(DependencyCatalog())

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

    def consultar_impacto(self, id_elemento: object) -> Alcance:
        return self._repositorio.obtener().impacto_de(id_elemento)

    def consultar_requisitos(self, id_elemento: object) -> Alcance:
        return self._repositorio.obtener().requisitos_de(id_elemento)

    def consultar_orden(self, id_elemento: object | None = None) -> OrdenProduccion:
        return self._repositorio.obtener().orden_de_preparacion(id_elemento)
