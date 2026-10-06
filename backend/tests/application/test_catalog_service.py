import pytest

from application import CatalogService, RedDependencias
from domain.dependency_catalog import (
    AutodependenciaError,
    CatalogRepository,
    DependenciaDuplicadaError,
    DependencyCatalog,
    ElementoDuplicadoError,
    ElementoNoEncontradoError,
    IdElementoInvalidoError,
    TipoElemento,
    TipoElementoInvalidoError,
)
from infrastructure import InMemoryCatalogRepository


class RepositorioEspia(CatalogRepository):
    """Repositorio de prueba que cuenta las llamadas a obtener y guardar."""

    def __init__(self) -> None:
        self._catalogo = DependencyCatalog()
        self.llamadas_obtener = 0
        self.llamadas_guardar = 0

    def obtener(self) -> DependencyCatalog:
        self.llamadas_obtener += 1
        return self._catalogo

    def guardar(self, catalogo: DependencyCatalog) -> None:
        self.llamadas_guardar += 1
        self._catalogo = catalogo


@pytest.fixture
def servicio() -> CatalogService:
    return CatalogService(InMemoryCatalogRepository())


@pytest.fixture
def servicio_cargado(servicio) -> CatalogService:
    servicio.crear_elemento("Silla", TipoElemento.PRODUCTO)
    servicio.crear_elemento("Madera", TipoElemento.INSUMO)
    servicio.crear_elemento("Tornillos", TipoElemento.INSUMO)
    servicio.crear_elemento("MaderasDelSur", TipoElemento.PROVEEDOR)
    servicio.crear_dependencia("Silla", "Madera")
    servicio.crear_dependencia("Silla", "Tornillos")
    servicio.crear_dependencia("Madera", "MaderasDelSur")
    return servicio


class TestConstruccion:
    def test_exige_un_repositorio_valido(self):
        with pytest.raises(TypeError):
            CatalogService("repositorio")  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            CatalogService(None)  # type: ignore[arg-type]

    def test_acepta_cualquier_implementacion_del_puerto(self):
        assert CatalogService(RepositorioEspia()) is not None


class TestCrearElemento:
    def test_registra_y_devuelve_el_elemento(self, servicio):
        elemento = servicio.crear_elemento("  Silla ", "producto")
        assert elemento.id == "Silla"
        assert elemento.tipo is TipoElemento.PRODUCTO

    def test_el_elemento_queda_disponible(self, servicio):
        servicio.crear_elemento("Silla", "PRODUCTO")
        assert servicio.obtener_elemento("silla").id == "Silla"

    def test_guarda_despues_de_crear(self):
        espia = RepositorioEspia()
        CatalogService(espia).crear_elemento("Silla", "PRODUCTO")
        assert espia.llamadas_guardar == 1

    def test_no_guarda_si_el_dominio_rechaza(self):
        espia = RepositorioEspia()
        with pytest.raises(TipoElementoInvalidoError):
            CatalogService(espia).crear_elemento("Mesa", "MUEBLE")
        assert espia.llamadas_guardar == 0

    @pytest.mark.parametrize(
        "id_elemento,tipo,error",
        [
            ("", "PRODUCTO", IdElementoInvalidoError),
            ("Silla", "MUEBLE", TipoElementoInvalidoError),
        ],
    )
    def test_propaga_los_errores_del_dominio(self, servicio, id_elemento, tipo, error):
        with pytest.raises(error):
            servicio.crear_elemento(id_elemento, tipo)

    def test_propaga_el_duplicado(self, servicio):
        servicio.crear_elemento("Silla", "PRODUCTO")
        with pytest.raises(ElementoDuplicadoError):
            servicio.crear_elemento("silla", "PRODUCTO")


class TestCrearDependencia:
    def test_registra_y_devuelve_la_dependencia(self, servicio):
        servicio.crear_elemento("Silla", "PRODUCTO")
        servicio.crear_elemento("Madera", "INSUMO")
        dependencia = servicio.crear_dependencia("Silla", "Madera")
        assert (dependencia.origen_id, dependencia.destino_id) == ("Silla", "Madera")

    def test_guarda_despues_de_crear(self):
        espia = RepositorioEspia()
        servicio = CatalogService(espia)
        servicio.crear_elemento("Silla", "PRODUCTO")
        servicio.crear_elemento("Madera", "INSUMO")
        espia.llamadas_guardar = 0
        servicio.crear_dependencia("Silla", "Madera")
        assert espia.llamadas_guardar == 1

    def test_no_guarda_si_el_dominio_rechaza(self, servicio_cargado):
        espia = RepositorioEspia()
        servicio = CatalogService(espia)
        servicio.crear_elemento("Silla", "PRODUCTO")
        espia.llamadas_guardar = 0
        with pytest.raises(ElementoNoEncontradoError):
            servicio.crear_dependencia("Silla", "Madera")
        assert espia.llamadas_guardar == 0

    def test_propaga_elemento_inexistente(self, servicio_cargado):
        with pytest.raises(ElementoNoEncontradoError):
            servicio_cargado.crear_dependencia("Mesa", "Madera")

    def test_propaga_dependencia_repetida(self, servicio_cargado):
        with pytest.raises(DependenciaDuplicadaError):
            servicio_cargado.crear_dependencia("Silla", "Madera")

    def test_propaga_autodependencia(self, servicio_cargado):
        with pytest.raises(AutodependenciaError):
            servicio_cargado.crear_dependencia("Silla", "Silla")


class TestLecturas:
    def test_catalogo_vacio_devuelve_listas_vacias(self, servicio):
        assert servicio.listar_elementos() == ()
        assert servicio.listar_dependencias() == ()

    def test_lista_elementos_en_orden_de_alta(self, servicio_cargado):
        assert [e.id for e in servicio_cargado.listar_elementos()] == [
            "Silla",
            "Madera",
            "Tornillos",
            "MaderasDelSur",
        ]

    def test_lista_dependencias_en_orden_estable(self, servicio_cargado):
        assert [str(d) for d in servicio_cargado.listar_dependencias()] == [
            "Silla requiere Madera",
            "Silla requiere Tornillos",
            "Madera requiere MaderasDelSur",
        ]

    def test_obtener_elemento_inexistente_lanza_error(self, servicio_cargado):
        with pytest.raises(ElementoNoEncontradoError):
            servicio_cargado.obtener_elemento("Mesa")

    def test_las_lecturas_no_guardan(self, servicio_cargado):
        espia = RepositorioEspia()
        servicio = CatalogService(espia)
        servicio.listar_elementos()
        servicio.listar_dependencias()
        servicio.obtener_red()
        assert espia.llamadas_guardar == 0


class TestRedDependencias:
    def test_devuelve_elementos_y_dependencias_juntos(self, servicio_cargado):
        red = servicio_cargado.obtener_red()
        assert isinstance(red, RedDependencias)
        assert red.total_elementos == 4
        assert red.total_dependencias == 3

    def test_la_red_es_consistente(self, servicio_cargado):
        red = servicio_cargado.obtener_red()
        ids = {e.id for e in red.elementos}
        for dependencia in red.dependencias:
            assert dependencia.origen_id in ids
            assert dependencia.destino_id in ids

    def test_incluye_elementos_aislados(self, servicio_cargado):
        servicio_cargado.crear_elemento("Barniz", "INSUMO")
        red = servicio_cargado.obtener_red()
        assert "Barniz" in {e.id for e in red.elementos}
        assert red.total_dependencias == 3

    def test_red_vacia(self, servicio):
        red = servicio.obtener_red()
        assert red.total_elementos == 0
        assert red.total_dependencias == 0
