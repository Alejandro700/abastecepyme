import pytest

from domain.dependency_catalog import (
    AutodependenciaError,
    Dependencia,
    DependenciaDuplicadaError,
    DependencyCatalog,
    Elemento,
    ElementoDuplicadoError,
    ElementoNoEncontradoError,
    IdElementoInvalidoError,
    TipoElemento,
    TipoElementoInvalidoError,
)


@pytest.fixture
def catalogo() -> DependencyCatalog:
    return DependencyCatalog()


@pytest.fixture
def catalogo_silla() -> DependencyCatalog:
    c = DependencyCatalog()
    c.registrar_elemento("Silla", TipoElemento.PRODUCTO)
    c.registrar_elemento("Madera", TipoElemento.INSUMO)
    c.registrar_elemento("Tornillos", TipoElemento.INSUMO)
    c.registrar_elemento("MaderasDelSur", TipoElemento.PROVEEDOR)
    c.registrar_dependencia("Silla", "Madera")
    c.registrar_dependencia("Silla", "Tornillos")
    c.registrar_dependencia("Madera", "MaderasDelSur")
    return c


class TestTipoElemento:
    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("PRODUCTO", TipoElemento.PRODUCTO),
            ("producto", TipoElemento.PRODUCTO),
            ("  Insumo  ", TipoElemento.INSUMO),
            ("pRoVeEdOr", TipoElemento.PROVEEDOR),
            (TipoElemento.INSUMO, TipoElemento.INSUMO),
        ],
    )
    def test_tolera_mayusculas_y_espacios(self, entrada, esperado):
        assert TipoElemento.desde_texto(entrada) is esperado

    @pytest.mark.parametrize("invalido", ["MUEBLE", "", "   ", None, 7])
    def test_rechaza_tipos_desconocidos(self, invalido):
        with pytest.raises(TipoElementoInvalidoError):
            TipoElemento.desde_texto(invalido)

    def test_el_error_enumera_las_opciones_validas(self):
        with pytest.raises(TipoElementoInvalidoError) as info:
            TipoElemento.desde_texto("MUEBLE")
        mensaje = str(info.value)
        assert "PRODUCTO" in mensaje and "INSUMO" in mensaje and "PROVEEDOR" in mensaje


class TestElemento:
    def test_crear_normaliza_la_entrada_del_usuario(self):
        elemento = Elemento.crear("  Silla  ", "producto")
        assert elemento.id == "Silla"
        assert elemento.tipo is TipoElemento.PRODUCTO

    def test_la_clave_no_distingue_mayusculas(self):
        assert Elemento.crear("Madera", "INSUMO").clave == Elemento.crear(
            "MADERA", "INSUMO"
        ).clave

    @pytest.mark.parametrize("invalido", ["", "   ", None, 42])
    def test_rechaza_ids_mal_formados(self, invalido):
        with pytest.raises(IdElementoInvalidoError):
            Elemento.crear(invalido, "PRODUCTO")

    def test_rechaza_id_demasiado_largo(self):
        with pytest.raises(IdElementoInvalidoError):
            Elemento.crear("X" * 121, "PRODUCTO")

    def test_el_elemento_es_inmutable(self):
        elemento = Elemento.crear("Silla", "PRODUCTO")
        with pytest.raises(Exception):
            elemento.id = "Mesa"  # type: ignore[misc]

    def test_el_constructor_directo_exige_datos_limpios(self):
        with pytest.raises(IdElementoInvalidoError):
            Elemento(id="  Silla  ", tipo=TipoElemento.PRODUCTO)
        with pytest.raises(IdElementoInvalidoError):
            Elemento(id="Silla", tipo="PRODUCTO")  # type: ignore[arg-type]


class TestRegistrarElementos:
    def test_catalogo_nuevo_esta_vacio(self, catalogo):
        assert catalogo.total_elementos() == 0
        assert catalogo.listar_elementos() == ()

    def test_registra_los_tres_tipos(self, catalogo):
        catalogo.registrar_elemento("Silla", "PRODUCTO")
        catalogo.registrar_elemento("Madera", "INSUMO")
        catalogo.registrar_elemento("MaderasDelSur", "PROVEEDOR")
        assert catalogo.total_elementos() == 3

    def test_devuelve_el_elemento_creado(self, catalogo):
        elemento = catalogo.registrar_elemento("  Silla ", "producto")
        assert elemento.id == "Silla"
        assert elemento.tipo is TipoElemento.PRODUCTO

    def test_rechaza_id_duplicado(self, catalogo):
        catalogo.registrar_elemento("Silla", "PRODUCTO")
        with pytest.raises(ElementoDuplicadoError):
            catalogo.registrar_elemento("Silla", "PRODUCTO")

    def test_rechaza_duplicado_aunque_cambie_el_tipo(self, catalogo):
        # El id es único en todo el catálogo, no por tipo.
        catalogo.registrar_elemento("Madera", "INSUMO")
        with pytest.raises(ElementoDuplicadoError):
            catalogo.registrar_elemento("Madera", "PROVEEDOR")

    @pytest.mark.parametrize("variante", ["madera", "MADERA", "MaDeRa", "  madera  "])
    def test_rechaza_duplicado_sin_distinguir_mayusculas(self, catalogo, variante):
        catalogo.registrar_elemento("Madera", "INSUMO")
        with pytest.raises(ElementoDuplicadoError):
            catalogo.registrar_elemento(variante, "INSUMO")

    def test_el_error_de_duplicado_menciona_el_id_original(self, catalogo):
        catalogo.registrar_elemento("Madera", "INSUMO")
        with pytest.raises(ElementoDuplicadoError) as info:
            catalogo.registrar_elemento("madera", "INSUMO")
        assert "Madera" in str(info.value)

    def test_el_rechazo_no_altera_el_catalogo(self, catalogo):
        catalogo.registrar_elemento("Silla", "PRODUCTO")
        for accion in (
            lambda: catalogo.registrar_elemento("silla", "PRODUCTO"),
            lambda: catalogo.registrar_elemento("Mesa", "MUEBLE"),
            lambda: catalogo.registrar_elemento("", "PRODUCTO"),
        ):
            with pytest.raises(Exception):
                accion()
        assert catalogo.total_elementos() == 1

    def test_lista_en_orden_de_registro(self, catalogo):
        for id_elemento in ("Silla", "Madera", "Tornillos"):
            catalogo.registrar_elemento(id_elemento, "INSUMO")
        assert [e.id for e in catalogo.listar_elementos()] == [
            "Silla",
            "Madera",
            "Tornillos",
        ]


class TestBuscarElementos:
    def test_encuentra_sin_distinguir_mayusculas(self, catalogo_silla):
        assert catalogo_silla.obtener_elemento("SILLA").id == "Silla"
        assert catalogo_silla.obtener_elemento("  silla  ").id == "Silla"

    def test_elemento_inexistente_lanza_error(self, catalogo_silla):
        with pytest.raises(ElementoNoEncontradoError):
            catalogo_silla.obtener_elemento("Mesa")

    def test_existe_elemento_responde_sin_lanzar(self, catalogo_silla):
        assert catalogo_silla.existe_elemento("silla") is True
        assert catalogo_silla.existe_elemento("Mesa") is False
        assert catalogo_silla.existe_elemento("") is False
        assert catalogo_silla.existe_elemento(None) is False


class TestRegistrarDependencias:
    def test_registra_una_dependencia(self, catalogo):
        catalogo.registrar_elemento("Silla", "PRODUCTO")
        catalogo.registrar_elemento("Madera", "INSUMO")
        dependencia = catalogo.registrar_dependencia("Silla", "Madera")
        assert dependencia == Dependencia("Silla", "Madera")
        assert catalogo.total_dependencias() == 1

    def test_la_direccion_es_a_requiere_b(self, catalogo_silla):
        dependencia = catalogo_silla.listar_dependencias()[0]
        assert dependencia.frase() == (
            "Para producir/preparar Silla necesito Madera"
        )

    def test_guarda_el_id_original_aunque_se_consulte_en_minuscula(self, catalogo):
        catalogo.registrar_elemento("Silla", "PRODUCTO")
        catalogo.registrar_elemento("Madera", "INSUMO")
        dependencia = catalogo.registrar_dependencia("silla", "MADERA")
        assert (dependencia.origen_id, dependencia.destino_id) == ("Silla", "Madera")

    def test_rechaza_dependencia_repetida(self, catalogo_silla):
        with pytest.raises(DependenciaDuplicadaError):
            catalogo_silla.registrar_dependencia("Silla", "Madera")
        assert catalogo_silla.total_dependencias() == 3

    def test_rechaza_repetida_escrita_distinto(self, catalogo_silla):
        with pytest.raises(DependenciaDuplicadaError):
            catalogo_silla.registrar_dependencia("SILLA", "madera")

    def test_rechaza_autodependencia(self, catalogo_silla):
        with pytest.raises(AutodependenciaError):
            catalogo_silla.registrar_dependencia("Silla", "Silla")

    def test_rechaza_autodependencia_escrita_distinto(self, catalogo_silla):
        with pytest.raises(AutodependenciaError):
            catalogo_silla.registrar_dependencia("Silla", "  silla  ")

    def test_rechaza_dependencia_con_origen_inexistente(self, catalogo_silla):
        with pytest.raises(ElementoNoEncontradoError):
            catalogo_silla.registrar_dependencia("Mesa", "Madera")

    def test_rechaza_dependencia_con_destino_inexistente(self, catalogo_silla):
        with pytest.raises(ElementoNoEncontradoError):
            catalogo_silla.registrar_dependencia("Silla", "Barniz")

    def test_permite_dependencia_entre_elementos_del_mismo_tipo(self, catalogo):
        # No se restringe qué tipo puede depender de qué tipo.
        catalogo.registrar_elemento("Tablero", "INSUMO")
        catalogo.registrar_elemento("Madera", "INSUMO")
        catalogo.registrar_dependencia("Tablero", "Madera")
        assert catalogo.total_dependencias() == 1

    def test_admite_dependencias_en_ambos_sentidos(self, catalogo):
        catalogo.registrar_elemento("A", "INSUMO")
        catalogo.registrar_elemento("B", "INSUMO")
        catalogo.registrar_dependencia("A", "B")
        catalogo.registrar_dependencia("B", "A")
        assert catalogo.total_dependencias() == 2

    def test_lista_dependencias_en_orden_estable(self, catalogo_silla):
        assert [str(d) for d in catalogo_silla.listar_dependencias()] == [
            "Silla requiere Madera",
            "Silla requiere Tornillos",
            "Madera requiere MaderasDelSur",
        ]


class TestRedDeDependencias:
    def test_el_caso_del_brief_queda_bien_representado(self, catalogo_silla):
        assert catalogo_silla.total_elementos() == 4
        assert catalogo_silla.total_dependencias() == 3

    def test_un_elemento_sin_dependencias_igual_aparece_en_la_red(self, catalogo_silla):
        catalogo_silla.registrar_elemento("Barniz", "INSUMO")
        ids = [e.id for e in catalogo_silla.listar_elementos()]
        assert "Barniz" in ids
        assert catalogo_silla.total_dependencias() == 3
