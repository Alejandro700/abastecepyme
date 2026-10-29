import pytest

from domain.dependency_catalog import (
    DependencyCatalog,
    ElementoNoEncontradoError,
    IdElementoInvalidoError,
    SentidoConsulta,
)


@pytest.fixture
def catalogo() -> DependencyCatalog:
    """Silla y Mesa requieren Madera; Silla también Tornillos; Madera requiere su proveedor."""
    catalogo = DependencyCatalog()
    for id_elemento, tipo in [
        ("Silla", "PRODUCTO"),
        ("Mesa", "PRODUCTO"),
        ("Madera", "INSUMO"),
        ("Tornillos", "INSUMO"),
        ("MaderasDelSur", "PROVEEDOR"),
        ("Suelto", "PROVEEDOR"),
    ]:
        catalogo.registrar_elemento(id_elemento, tipo)
    for origen, destino in [
        ("Silla", "Madera"),
        ("Silla", "Tornillos"),
        ("Mesa", "Madera"),
        ("Madera", "MaderasDelSur"),
    ]:
        catalogo.registrar_dependencia(origen, destino)
    return catalogo


def _ids(alcance) -> list[str]:
    return [a.elemento.id for a in alcance.alcanzados]


class TestImpacto:
    def test_un_proveedor_afecta_toda_la_cadena_hacia_los_productos(self, catalogo):
        alcance = catalogo.impacto_de("MaderasDelSur")

        assert alcance.sentido is SentidoConsulta.IMPACTO
        assert _ids(alcance) == ["Madera", "Mesa", "Silla"]
        assert alcance.total == 3

    def test_los_niveles_indican_si_la_relacion_es_directa(self, catalogo):
        alcance = catalogo.impacto_de("MaderasDelSur")

        assert {a.elemento.id: a.nivel for a in alcance.alcanzados} == {
            "Madera": 1,
            "Mesa": 2,
            "Silla": 2,
        }

    def test_la_cadena_se_lee_a_favor_de_las_flechas(self, catalogo):
        silla = next(
            a for a in catalogo.impacto_de("MaderasDelSur").alcanzados
            if a.elemento.id == "Silla"
        )

        assert silla.cadena == ("Silla", "Madera", "MaderasDelSur")
        assert silla.explicacion() == "Silla requiere Madera, que requiere MaderasDelSur"

    def test_un_insumo_afecta_solo_a_quienes_lo_usan(self, catalogo):
        assert _ids(catalogo.impacto_de("Tornillos")) == ["Silla"]

    def test_un_producto_que_nadie_requiere_no_afecta_a_nadie(self, catalogo):
        alcance = catalogo.impacto_de("Silla")

        assert alcance.alcanzados == ()
        assert alcance.total == 0

    def test_un_elemento_sin_relaciones_no_afecta_a_nadie(self, catalogo):
        assert catalogo.impacto_de("Suelto").total == 0

    def test_no_distingue_mayusculas_ni_espacios(self, catalogo):
        assert _ids(catalogo.impacto_de("  maderasdelsur ")) == ["Madera", "Mesa", "Silla"]

    def test_conserva_el_tipo_de_cada_elemento_alcanzado(self, catalogo):
        tipos = {a.elemento.id: a.elemento.tipo.value for a in catalogo.impacto_de("Tornillos").alcanzados}

        assert tipos == {"Silla": "PRODUCTO"}

    def test_elemento_inexistente_lanza_error_de_catalogo(self, catalogo):
        with pytest.raises(ElementoNoEncontradoError):
            catalogo.impacto_de("Pata")

    def test_id_mal_formado_lanza_error_de_id(self, catalogo):
        with pytest.raises(IdElementoInvalidoError):
            catalogo.impacto_de("   ")

    def test_refleja_las_dependencias_nuevas(self, catalogo):
        assert catalogo.impacto_de("Tornillos").total == 1

        catalogo.registrar_dependencia("Mesa", "Tornillos")

        assert _ids(catalogo.impacto_de("Tornillos")) == ["Mesa", "Silla"]

    def test_con_un_ciclo_termina_y_no_se_incluye_a_si_mismo(self):
        catalogo = DependencyCatalog()
        catalogo.registrar_elemento("A", "INSUMO")
        catalogo.registrar_elemento("B", "INSUMO")
        catalogo.registrar_dependencia("A", "B")
        catalogo.registrar_dependencia("B", "A")

        assert _ids(catalogo.impacto_de("A")) == ["B"]


class TestRequisitos:
    def test_un_producto_necesita_toda_su_cadena_hacia_los_proveedores(self, catalogo):
        alcance = catalogo.requisitos_de("Silla")

        assert alcance.sentido is SentidoConsulta.REQUISITOS
        assert _ids(alcance) == ["Madera", "Tornillos", "MaderasDelSur"]

    def test_la_cadena_empieza_en_el_elemento_consultado(self, catalogo):
        proveedor = catalogo.requisitos_de("Silla").alcanzados[-1]

        assert proveedor.cadena == ("Silla", "Madera", "MaderasDelSur")
        assert proveedor.nivel == 2

    def test_un_proveedor_no_requiere_nada(self, catalogo):
        assert catalogo.requisitos_de("MaderasDelSur").total == 0

    def test_elemento_inexistente_lanza_error_de_catalogo(self, catalogo):
        with pytest.raises(ElementoNoEncontradoError):
            catalogo.requisitos_de("Pata")


class TestDireccion:
    def test_impacto_y_requisitos_son_consultas_opuestas(self, catalogo):
        assert catalogo.impacto_de("Silla").total == 0
        assert catalogo.requisitos_de("Silla").total == 3

        assert catalogo.impacto_de("MaderasDelSur").total == 3
        assert catalogo.requisitos_de("MaderasDelSur").total == 0

    def test_consultar_no_modifica_el_catalogo(self, catalogo):
        antes = (catalogo.total_elementos(), catalogo.total_dependencias())

        catalogo.impacto_de("MaderasDelSur")
        catalogo.requisitos_de("Silla")

        assert (catalogo.total_elementos(), catalogo.total_dependencias()) == antes
