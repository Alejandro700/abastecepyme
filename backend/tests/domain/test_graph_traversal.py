import pytest

from domain.graph import DirectedGraph, Node, NodeNotFoundError


def _grafo(nodos: str, aristas: list[tuple[str, str]]) -> DirectedGraph:
    grafo = DirectedGraph()
    for nodo in nodos:
        grafo.add_node(Node(nodo))
    for origen, destino in aristas:
        grafo.add_edge(origen, destino)
    return grafo


@pytest.fixture
def cadena() -> DirectedGraph:
    """A -> B -> C -> D."""
    return _grafo("ABCD", [("A", "B"), ("B", "C"), ("C", "D")])


class TestDescendants:
    def test_sigue_la_cadena_con_distancia_y_camino(self, cadena):
        visitas = cadena.descendants("A")

        assert [v.node_id for v in visitas] == ["B", "C", "D"]
        assert [v.depth for v in visitas] == [1, 2, 3]
        assert visitas[-1].path == ("A", "B", "C", "D")

    def test_desde_la_mitad_solo_ve_lo_que_sigue(self, cadena):
        assert [v.node_id for v in cadena.descendants("C")] == ["D"]

    def test_un_nodo_sin_salidas_devuelve_vacio(self, cadena):
        assert cadena.descendants("D") == ()

    def test_un_nodo_aislado_devuelve_vacio(self):
        assert _grafo("AB", []).descendants("A") == ()

    def test_nodo_inexistente_lanza_error(self, cadena):
        with pytest.raises(NodeNotFoundError):
            cadena.descendants("Z")

    def test_no_incluye_el_nodo_de_partida(self, cadena):
        assert "A" not in [v.node_id for v in cadena.descendants("A")]

    def test_ordena_por_cercania_y_luego_alfabeticamente(self):
        grafo = _grafo(
            "ABCDE", [("A", "C"), ("A", "B"), ("B", "D"), ("C", "E")]
        )

        assert [v.node_id for v in grafo.descendants("A")] == ["B", "C", "D", "E"]

    def test_visita_cada_nodo_una_vez_por_su_camino_mas_corto(self):
        grafo = _grafo(
            "ABCD", [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("A", "D")]
        )

        d = next(v for v in grafo.descendants("A") if v.node_id == "D")

        assert d.depth == 1
        assert d.path == ("A", "D")
        assert [v.node_id for v in grafo.descendants("A")].count("D") == 1

    def test_con_un_rombo_no_repite_el_nodo_final(self):
        grafo = _grafo("ABCD", [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

        visitas = grafo.descendants("A")

        assert [v.node_id for v in visitas] == ["B", "C", "D"]
        assert visitas[-1].path == ("A", "B", "D")

    def test_termina_aunque_haya_un_ciclo(self):
        grafo = _grafo("ABC", [("A", "B"), ("B", "C"), ("C", "A")])

        visitas = grafo.descendants("A")

        assert [v.node_id for v in visitas] == ["B", "C"]

    def test_no_modifica_el_grafo(self, cadena):
        cadena.descendants("A")
        cadena.ancestors("D")

        assert cadena.node_count() == 4
        assert cadena.edge_count() == 3


class TestAncestors:
    def test_recorre_las_flechas_al_reves(self, cadena):
        visitas = cadena.ancestors("D")

        assert [v.node_id for v in visitas] == ["C", "B", "A"]
        assert [v.depth for v in visitas] == [1, 2, 3]
        assert visitas[-1].path == ("D", "C", "B", "A")

    def test_un_nodo_que_nadie_requiere_devuelve_vacio(self, cadena):
        assert cadena.ancestors("A") == ()

    def test_nodo_inexistente_lanza_error(self, cadena):
        with pytest.raises(NodeNotFoundError):
            cadena.ancestors("Z")

    def test_junta_todos_los_caminos_que_llegan_al_nodo(self):
        grafo = _grafo("ABCD", [("A", "C"), ("B", "C"), ("C", "D")])

        assert [v.node_id for v in grafo.ancestors("D")] == ["C", "A", "B"]

    def test_termina_aunque_haya_un_ciclo(self):
        grafo = _grafo("ABC", [("A", "B"), ("B", "C"), ("C", "A")])

        assert [v.node_id for v in grafo.ancestors("A")] == ["C", "B"]
