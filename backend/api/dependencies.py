

from application import CatalogService
from infrastructure import InMemoryCatalogRepository


_repositorio = InMemoryCatalogRepository()


def get_catalog_service() -> CatalogService:

    return CatalogService(_repositorio)


def reiniciar_repositorio() -> None:
    _repositorio.reiniciar()
