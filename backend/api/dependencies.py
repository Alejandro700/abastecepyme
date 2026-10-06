from application import CatalogService
from infrastructure import InMemoryCatalogRepository

_repositorio = InMemoryCatalogRepository()


def get_catalog_service() -> CatalogService:
    """Entrega el servicio del catálogo sobre el repositorio en memoria."""
    return CatalogService(_repositorio)


def reiniciar_repositorio() -> None:
    _repositorio.reiniciar()
