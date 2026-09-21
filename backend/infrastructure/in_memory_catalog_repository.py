

from domain.dependency_catalog import CatalogRepository, DependencyCatalog


class InMemoryCatalogRepository(CatalogRepository):

    def __init__(self, catalogo: DependencyCatalog | None = None) -> None:

        if catalogo is not None and not isinstance(catalogo, DependencyCatalog):
            raise TypeError(
                f"Se esperaba un DependencyCatalog, se recibió "
                f"{type(catalogo).__name__}."
            )
        self._catalogo = catalogo if catalogo is not None else DependencyCatalog()

    def obtener(self) -> DependencyCatalog:

        return self._catalogo

    def guardar(self, catalogo: DependencyCatalog) -> None:

        if not isinstance(catalogo, DependencyCatalog):
            raise TypeError(
                f"Se esperaba un DependencyCatalog, se recibió "
                f"{type(catalogo).__name__}."
            )
        self._catalogo = catalogo

    def reiniciar(self) -> None:

        self._catalogo = DependencyCatalog()

    def __repr__(self) -> str:
        return f"InMemoryCatalogRepository({self._catalogo!r})"
