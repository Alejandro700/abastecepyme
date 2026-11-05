import pytest

from domain.graph import CycleError, DirectedGraph, Node, NodeNotFoundError


def _grafo(nodos: str, aristas: list[tuple[str, str]]) -> DirectedGraph:
    grafo = DirectedGraph()
    for nodo in nodos:
        grafo.add_node(Node(nodo))
    for origen, destino in aristas:
        grafo.add_edge(origen, destino)
    return grafo


class TestCapasSinCiclo:
    def test_lo_que_no_requiere_nada_va_primero(self):
        grafo = _grafo("ABC", [("A", "B"), ("B", "C")])

        assert grafo.build_layers() == (("C",), ("B",), ("A",))

    def test_los_nodos_independientes_comparten_capa_en_orden_alfabetico(self):
        grafo = _grafo("ABCD", [("A", "D"), ("B", "D"), ("C", "D")])

        assert grafo.build_layers() == (("D",), ("A", "B", "C"))

    def test_rombo(self):
        grafo = _grafo("ABCD", [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

        assert grafo.build_layers() == (("D",), ("B", "C"), ("A",))

    def test_un_nodo_espera_a_su_requisito_mas_lejano(self):
        grafo = _grafo("ABC", [("A", "B"), ("B", "C"), ("A", "C")])

        assert grafo.build_layers() == (("C",), ("B",), ("A",))

    def test_los_nodos_aislados_van_en_la_primera_capa(self):
        grafo = _grafo("ABZ", [("A", "B")])

        assert grafo.build_layers() == (("B", "Z"), ("A",))

    def test_un_grafo_vacio_no_tiene_capas(self):
        assert DirectedGraph().build_layers() == ()

    def test_cada_nodo_aparece_una_vez_y_despues_de_sus_requisitos(self):
        grafo = _grafo(
            "ABCDEFG",
            [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E"), ("F", "E")],
        )

        capas = grafo.build_layers()
        posicion = {n: i for i, capa in enumerate(capas) for n in capa}

        assert sorted(posicion) == sorted("ABCDEFG")
        assert sum(len(capa) for capa in capas) == 7
        for arista in grafo.edges():
            assert posicion[arista.target_id] < posicion[arista.source_id]

    def test_no_modifica_el_grafo(self):
        grafo = _grafo("ABC", [("A", "B"), ("B", "C")])

        grafo.build_layers()

        assert grafo.node_count() == 3
        assert grafo.edge_count() == 2


class TestSubconjunto:
    def test_ordena_solo_los_nodos_indicados(self):
        grafo = _grafo("ABC", [("A", "B"), ("B", "C")])

        assert grafo.build_layers(only={"B", "C"}) == (("C",), ("B",))

    def test_ignora_las_aristas_que_salen_del_subconjunto(self):
        grafo = _grafo("ABC", [("A", "B"), ("A", "C")])

        assert grafo.build_layers(only={"A", "B"}) == (("B",), ("A",))

    def test_un_nodo_inexistente_lanza_error(self):
        grafo = _grafo("AB", [("A", "B")])

        with pytest.raises(NodeNotFoundError):
            grafo.build_layers(only={"A", "Z"})

    def test_un_ciclo_fuera_del_subconjunto_no_lo_bloquea(self):
        grafo = _grafo("ABXY", [("A", "B"), ("X", "Y"), ("Y", "X")])

        assert grafo.build_layers(only={"A", "B"}) == (("B",), ("A",))


class TestCiclos:
    def test_un_ciclo_simple_se_reporta_cerrado(self):
        grafo = _grafo("AB", [("A", "B"), ("B", "A")])

        with pytest.raises(CycleError) as info:
            grafo.build_layers()

        assert info.value.cycle == ("A", "B", "A")
        assert info.value.blocked == ("A", "B")

    def test_un_ciclo_de_tres(self):
        grafo = _grafo("ABC", [("A", "B"), ("B", "C"), ("C", "A")])

        with pytest.raises(CycleError) as info:
            grafo.build_layers()

        assert info.value.cycle == ("A", "B", "C", "A")

    def test_el_ciclo_reportado_existe_de_verdad(self):
        grafo = _grafo(
            "ABCDE", [("A", "B"), ("B", "C"), ("C", "B"), ("D", "A"), ("A", "E")]
        )

        with pytest.raises(CycleError) as info:
            grafo.build_layers()

        ciclo = info.value.cycle
        assert ciclo[0] == ciclo[-1]
        for origen, destino in zip(ciclo, ciclo[1:]):
            assert grafo.has_edge(origen, destino)

    def test_lo_que_depende_de_un_ciclo_queda_bloqueado(self):
        grafo = _grafo("ABCD", [("A", "B"), ("B", "A"), ("C", "A"), ("C", "D")])

        with pytest.raises(CycleError) as info:
            grafo.build_layers()

        assert info.value.blocked == ("A", "B", "C")
        assert "D" not in info.value.blocked

    def test_un_nodo_que_se_requiere_a_si_mismo_es_un_ciclo(self):
        grafo = _grafo("A", [("A", "A")])

        with pytest.raises(CycleError) as info:
            grafo.build_layers()

        assert info.value.cycle == ("A", "A")

    def test_el_mensaje_nombra_el_ciclo(self):
        grafo = _grafo("AB", [("A", "B"), ("B", "A")])

        with pytest.raises(CycleError, match="A -> B -> A"):
            grafo.build_layers()
