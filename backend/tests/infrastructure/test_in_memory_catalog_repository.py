import pytest

from domain.dependency_catalog import (
    CatalogRepository,
    DependencyCatalog,
    TipoElemento,
)
from infrastructure import InMemoryCatalogRepository


@pytest.fixture
def repositorio() -> InMemoryCatalogRepository:
    return InMemoryCatalogRepository()


@pytest.fixture
def catalogo_cargado() -> DependencyCatalog:
    catalogo = DependencyCatalog()
    catalogo.registrar_elemento("Silla", TipoElemento.PRODUCTO)
    catalogo.registrar_elemento("Madera", TipoElemento.INSUMO)
    catalogo.registrar_dependencia("Silla", "Madera")
    return catalogo


class TestContrato:
    def test_implementa_el_puerto(self, repositorio):
        assert isinstance(repositorio, CatalogRepository)

    def test_el_puerto_no_se_puede_instanciar(self):
        with pytest.raises(TypeError):
            CatalogRepository()  # type: ignore[abstract]

    def test_una_implementacion_incompleta_no_se_puede_instanciar(self):
        class RepositorioAMedias(CatalogRepository):
            def obtener(self) -> DependencyCatalog:
                return DependencyCatalog()

        with pytest.raises(TypeError):
            RepositorioAMedias()  # type: ignore[abstract]


class TestObtener:
    def test_repositorio_nuevo_devuelve_catalogo_vacio(self, repositorio):
        catalogo = repositorio.obtener()
        assert isinstance(catalogo, DependencyCatalog)
        assert catalogo.total_elementos() == 0

    def test_devuelve_siempre_la_misma_instancia(self, repositorio):
        assert repositorio.obtener() is repositorio.obtener()

    def test_dos_repositorios_no_comparten_estado(self):
        uno, otro = InMemoryCatalogRepository(), InMemoryCatalogRepository()
        uno.obtener().registrar_elemento("Silla", TipoElemento.PRODUCTO)
        assert otro.obtener().total_elementos() == 0


class TestGuardar:
    def test_guarda_y_recupera_un_catalogo(self, repositorio, catalogo_cargado):
        repositorio.guardar(catalogo_cargado)
        recuperado = repositorio.obtener()
        assert recuperado.total_elementos() == 2
        assert recuperado.total_dependencias() == 1

    def test_guardar_reemplaza_lo_anterior(self, repositorio, catalogo_cargado):
        repositorio.guardar(catalogo_cargado)
        repositorio.guardar(DependencyCatalog())
        assert repositorio.obtener().total_elementos() == 0

    def test_los_cambios_sobre_el_catalogo_obtenido_persisten(self, repositorio):
        # Devuelve el objeto vivo; con una base de datos no sería así.
        repositorio.obtener().registrar_elemento("Silla", TipoElemento.PRODUCTO)
        assert repositorio.obtener().total_elementos() == 1

    @pytest.mark.parametrize("basura", [None, "catalogo", 42, {}])
    def test_rechaza_lo_que_no_sea_un_catalogo(self, repositorio, basura):
        with pytest.raises(TypeError):
            repositorio.guardar(basura)

    def test_el_rechazo_no_pierde_lo_guardado(self, repositorio, catalogo_cargado):
        repositorio.guardar(catalogo_cargado)
        with pytest.raises(TypeError):
            repositorio.guardar("basura")
        assert repositorio.obtener().total_elementos() == 2


class TestConstruccion:
    def test_admite_un_catalogo_inicial(self, catalogo_cargado):
        repositorio = InMemoryCatalogRepository(catalogo_cargado)
        assert repositorio.obtener() is catalogo_cargado

    def test_rechaza_un_inicial_invalido(self):
        with pytest.raises(TypeError):
            InMemoryCatalogRepository("catalogo")  # type: ignore[arg-type]


class TestReiniciar:
    def test_vacia_el_repositorio(self, repositorio, catalogo_cargado):
        repositorio.guardar(catalogo_cargado)
        repositorio.reiniciar()
        assert repositorio.obtener().total_elementos() == 0

    def test_no_forma_parte_del_puerto(self):
        assert not hasattr(CatalogRepository, "reiniciar")
