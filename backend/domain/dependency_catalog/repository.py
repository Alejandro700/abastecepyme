

from abc import ABC, abstractmethod

from .dependency_catalog import DependencyCatalog


class CatalogRepository(ABC):

    @abstractmethod
    def obtener(self) -> DependencyCatalog:

        raise NotImplementedError

    @abstractmethod
    def guardar(self, catalogo: DependencyCatalog) -> None:

        raise NotImplementedError
