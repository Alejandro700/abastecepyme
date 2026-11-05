import pytest

from domain.dependency_catalog import (
    CicloDetectadoError,
    DependencyCatalog,
    ElementoNoEncontradoError,
    IdElementoInvalidoError,
)


def _catalogo(elementos: list[tuple[str, str]], deps: list[tuple[str, str]]):
    catalogo = DependencyCatalog()
    for id_elemento, tipo in elementos:
        catalogo.registrar_elemento(id_elemento, tipo)
    for origen, destino in deps:
        catalogo.registrar_dependencia(origen, destino)
    return catalogo


@pytest.fixture
def catalogo() -> DependencyCatalog:
    """Silla y Mesa requieren Madera; Silla también Tornillos; Madera requiere su proveedor."""
    return _catalogo(
        [
            ("Silla", "PRODUCTO"),
            ("Mesa", "PRODUCTO"),
            ("Madera", "INSUMO"),
            ("Tornillos", "INSUMO"),
            ("MaderasDelSur", "PROVEEDOR"),
            ("Suelto", "PROVEEDOR"),
        ],
        [
            ("Silla", "Madera"),
            ("Silla", "Tornillos"),
            ("Mesa", "Madera"),
            ("Madera", "MaderasDelSur"),
        ],
    )


def _etapas(orden) -> list[list[str]]:
    return [[e.id for e in etapa.elementos] for etapa in orden.etapas]


class TestOrdenGlobal:
    def test_agrupa_por_etapas_empezando_por_lo_que_no_requiere_nada(self, catalogo):
        orden = catalogo.orden_de_preparacion()

        assert _etapas(orden) == [
            ["MaderasDelSur", "Suelto", "Tornillos"],
            ["Madera"],
            ["Mesa", "Silla"],
        ]

    def test_las_etapas_se_numeran_desde_uno(self, catalogo):
        orden = catalogo.orden_de_preparacion()

        assert [etapa.numero for etapa in orden.etapas] == [1, 2, 3]

    def test_incluye_todos_los_elementos_una_sola_vez(self, catalogo):
        orden = catalogo.orden_de_preparacion()

        assert orden.total_elementos == catalogo.total_elementos()
        assert sorted(e.id for e in orden.secuencia) == sorted(
            e.id for e in catalogo.listar_elementos()
        )

    def test_la_secuencia_respeta_cada_dependencia(self, catalogo):
        posicion = {e.id: i for i, e in enumerate(catalogo.orden_de_preparacion().secuencia)}

        for dependencia in catalogo.listar_dependencias():
            assert posicion[dependencia.destino_id] < posicion[dependencia.origen_id]

    def test_no_hay_objetivo_cuando_se_ordena_toda_la_red(self, catalogo):
        assert catalogo.orden_de_preparacion().objetivo is None

    def test_un_catalogo_vacio_no_tiene_etapas(self):
        orden = DependencyCatalog().orden_de_preparacion()

        assert orden.etapas == ()
        assert orden.total_elementos == 0

    def test_refleja_las_dependencias_nuevas(self, catalogo):
        catalogo.registrar_dependencia("Suelto", "MaderasDelSur")

        orden = catalogo.orden_de_preparacion()

        assert _etapas(orden)[0] == ["MaderasDelSur", "Tornillos"]
        assert "Suelto" in _etapas(orden)[1]

    def test_consultar_no_modifica_el_catalogo(self, catalogo):
        antes = (catalogo.total_elementos(), catalogo.total_dependencias())

        catalogo.orden_de_preparacion()

        assert (catalogo.total_elementos(), catalogo.total_dependencias()) == antes


class TestOrdenParaProducir:
    def test_solo_incluye_lo_que_el_elemento_necesita(self, catalogo):
        orden = catalogo.orden_de_preparacion("Silla")

        assert _etapas(orden) == [["MaderasDelSur", "Tornillos"], ["Madera"], ["Silla"]]
        assert orden.objetivo.id == "Silla"

    def test_el_elemento_consultado_va_solo_en_la_ultima_etapa(self, catalogo):
        orden = catalogo.orden_de_preparacion("Mesa")

        assert _etapas(orden)[-1] == ["Mesa"]

    def test_un_proveedor_se_ordena_solo(self, catalogo):
        assert _etapas(catalogo.orden_de_preparacion("MaderasDelSur")) == [["MaderasDelSur"]]

    def test_no_distingue_mayusculas(self, catalogo):
        assert catalogo.orden_de_preparacion(" silla ").objetivo.id == "Silla"

    def test_elemento_inexistente_lanza_error_de_catalogo(self, catalogo):
        with pytest.raises(ElementoNoEncontradoError):
            catalogo.orden_de_preparacion("Pata")

    def test_id_mal_formado_lanza_error_de_id(self, catalogo):
        with pytest.raises(IdElementoInvalidoError):
            catalogo.orden_de_preparacion("   ")


class TestCiclos:
    @pytest.fixture
    def con_ciclo(self, catalogo) -> DependencyCatalog:
        catalogo.registrar_dependencia("MaderasDelSur", "Silla")
        return catalogo

    def test_un_ciclo_impide_el_orden(self, con_ciclo):
        with pytest.raises(CicloDetectadoError):
            con_ciclo.orden_de_preparacion()

    def test_reporta_el_ciclo_concreto_y_cerrado(self, con_ciclo):
        with pytest.raises(CicloDetectadoError) as info:
            con_ciclo.orden_de_preparacion()

        assert info.value.ciclo == ("Madera", "MaderasDelSur", "Silla", "Madera")

    def test_la_explicacion_se_lee_como_una_frase(self, con_ciclo):
        with pytest.raises(CicloDetectadoError) as info:
            con_ciclo.orden_de_preparacion()

        assert info.value.explicacion == (
            "Madera requiere MaderasDelSur, que requiere Silla, que requiere Madera"
        )
        assert info.value.explicacion in str(info.value)

    def test_lista_tambien_lo_que_queda_bloqueado(self, con_ciclo):
        with pytest.raises(CicloDetectadoError) as info:
            con_ciclo.orden_de_preparacion()

        assert info.value.bloqueados == ("Madera", "MaderasDelSur", "Mesa", "Silla")

    def test_un_ciclo_en_la_cadena_del_elemento_lo_bloquea(self, con_ciclo):
        with pytest.raises(CicloDetectadoError):
            con_ciclo.orden_de_preparacion("Silla")

    def test_un_ciclo_ajeno_no_bloquea_el_orden_de_otro_elemento(self, catalogo):
        catalogo.registrar_elemento("X", "INSUMO")
        catalogo.registrar_elemento("Y", "INSUMO")
        catalogo.registrar_dependencia("X", "Y")
        catalogo.registrar_dependencia("Y", "X")

        with pytest.raises(CicloDetectadoError):
            catalogo.orden_de_preparacion()
        assert _etapas(catalogo.orden_de_preparacion("Silla"))[-1] == ["Silla"]
