from abc import ABC, abstractmethod

from .dependency_catalog import DependencyCatalog


class CatalogRepository(ABC):
    """Puerto de persistencia del catálogo."""

    @abstractmethod
    def obtener(self) -> DependencyCatalog:
        """Devuelve el catálogo actual."""

        raise NotImplementedError

    @abstractmethod
    def guardar(self, catalogo: DependencyCatalog) -> None:
        """Persiste el catálogo."""

        raise NotImplementedError
