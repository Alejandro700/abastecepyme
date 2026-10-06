import pytest

from domain.graph import (
    DirectedGraph,
    DuplicateEdgeError,
    DuplicateNodeError,
    Edge,
    InvalidNodeIdError,
    Node,
    NodeNotFoundError,
)


@pytest.fixture
def grafo() -> DirectedGraph:
    return DirectedGraph()


@pytest.fixture
def grafo_abc() -> DirectedGraph:
    """Grafo con A -> B -> C ya cargado."""
    g = DirectedGraph()
    for node_id in ("A", "B", "C"):
        g.add_node(Node(node_id))
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    return g


class TestNode:
    def test_nodo_valido_conserva_su_id(self):
        assert Node("A").id == "A"

    def test_dos_nodos_con_el_mismo_id_son_iguales(self):
        assert Node("A") == Node("A")
        assert len({Node("A"), Node("A")}) == 1

    def test_el_nodo_es_inmutable(self):
        nodo = Node("A")
        with pytest.raises(Exception):
            nodo.id = "B"  # type: ignore[misc]

    @pytest.mark.parametrize(
        "id_invalido",
        ["", "   ", " A", "A ", " A "],
        ids=["vacio", "solo-espacios", "espacio-inicio", "espacio-final", "ambos"],
    )
    def test_rechaza_ids_mal_formados(self, id_invalido):
        with pytest.raises(InvalidNodeIdError):
            Node(id_invalido)

    @pytest.mark.parametrize("no_texto", [None, 42, 3.14, ["A"]])
    def test_rechaza_ids_que_no_son_texto(self, no_texto):
        with pytest.raises(InvalidNodeIdError):
            Node(no_texto)  # type: ignore[arg-type]


class TestEdge:
    def test_guarda_origen_y_destino(self):
        arista = Edge("A", "B")
        assert (arista.source_id, arista.target_id) == ("A", "B")

    def test_la_direccion_importa(self):
        assert Edge("A", "B") != Edge("B", "A")

    def test_rechaza_extremos_mal_formados(self):
        with pytest.raises(InvalidNodeIdError):
            Edge("", "B")
        with pytest.raises(InvalidNodeIdError):
            Edge("A", "  ")


class TestAgregarNodos:
    def test_grafo_nuevo_esta_vacio(self, grafo):
        assert grafo.node_count() == 0
        assert grafo.edge_count() == 0
        assert grafo.nodes() == ()

    def test_agrega_y_encuentra_un_nodo(self, grafo):
        grafo.add_node(Node("A"))
        assert grafo.has_node("A")
        assert grafo.get_node("A") == Node("A")
        assert grafo.node_count() == 1

    def test_rechaza_nodo_duplicado(self, grafo):
        grafo.add_node(Node("A"))
        with pytest.raises(DuplicateNodeError):
            grafo.add_node(Node("A"))

    def test_el_duplicado_no_altera_el_grafo(self, grafo):
        grafo.add_node(Node("A"))
        grafo.add_node(Node("B"))
        grafo.add_edge("A", "B")
        with pytest.raises(DuplicateNodeError):
            grafo.add_node(Node("A"))
        assert grafo.node_count() == 2
        assert grafo.edge_count() == 1

    def test_el_id_distingue_mayusculas(self, grafo):
        # El grafo no normaliza: 'A' y 'a' son nodos distintos.
        grafo.add_node(Node("A"))
        grafo.add_node(Node("a"))
        assert grafo.node_count() == 2

    def test_nodo_inexistente_lanza_error(self, grafo):
        with pytest.raises(NodeNotFoundError):
            grafo.get_node("Z")
        assert grafo.has_node("Z") is False

    def test_lista_nodos_en_orden_de_insercion(self, grafo):
        for node_id in ("C", "A", "B"):
            grafo.add_node(Node(node_id))
        assert [n.id for n in grafo.nodes()] == ["C", "A", "B"]

    def test_rechaza_algo_que_no_es_nodo(self, grafo):
        with pytest.raises(TypeError):
            grafo.add_node("A")  # type: ignore[arg-type]


class TestAgregarAristas:
    def test_agrega_una_arista(self, grafo):
        grafo.add_node(Node("A"))
        grafo.add_node(Node("B"))
        arista = grafo.add_edge("A", "B")
        assert arista == Edge("A", "B")
        assert grafo.has_edge("A", "B")
        assert grafo.edge_count() == 1

    def test_la_arista_es_dirigida(self, grafo_abc):
        assert grafo_abc.has_edge("A", "B")
        assert grafo_abc.has_edge("B", "A") is False

    def test_rechaza_arista_duplicada(self, grafo_abc):
        with pytest.raises(DuplicateEdgeError):
            grafo_abc.add_edge("A", "B")
        assert grafo_abc.edge_count() == 2

    def test_rechaza_arista_con_origen_inexistente(self, grafo):
        grafo.add_node(Node("B"))
        with pytest.raises(NodeNotFoundError):
            grafo.add_edge("A", "B")

    def test_rechaza_arista_con_destino_inexistente(self, grafo):
        grafo.add_node(Node("A"))
        with pytest.raises(NodeNotFoundError):
            grafo.add_edge("A", "B")

    def test_no_crea_nodos_implicitos(self, grafo):
        grafo.add_node(Node("A"))
        with pytest.raises(NodeNotFoundError):
            grafo.add_edge("A", "Z")
        assert grafo.node_count() == 1

    def test_rechaza_extremos_mal_formados(self, grafo_abc):
        with pytest.raises(InvalidNodeIdError):
            grafo_abc.add_edge("", "B")

    def test_has_edge_no_lanza_con_nodos_inexistentes(self, grafo):
        assert grafo.has_edge("X", "Y") is False

    def test_el_grafo_admite_autociclo(self, grafo):
        # A -> A es válido en el grafo; prohibirlo es regla del catálogo.
        grafo.add_node(Node("A"))
        grafo.add_edge("A", "A")
        assert grafo.has_edge("A", "A")

    def test_lista_aristas_en_orden_estable(self, grafo):
        for node_id in ("A", "B", "C", "D"):
            grafo.add_node(Node(node_id))
        grafo.add_edge("A", "D")
        grafo.add_edge("A", "B")
        grafo.add_edge("A", "C")
        # Nodos en orden de inserción; destinos en orden alfabético.
        assert [str(e) for e in grafo.edges()] == [
            "A -> B",
            "A -> C",
            "A -> D",
        ]


class TestVecindad:
    def test_sucesores_son_lo_que_el_nodo_requiere(self, grafo_abc):
        assert grafo_abc.successors("A") == frozenset({"B"})
        assert grafo_abc.successors("C") == frozenset()

    def test_predecesores_son_quienes_lo_requieren(self, grafo_abc):
        assert grafo_abc.predecessors("B") == frozenset({"A"})
        assert grafo_abc.predecessors("A") == frozenset()

    def test_las_dos_vistas_se_mantienen_sincronizadas(self, grafo):
        for node_id in ("A", "B", "C"):
            grafo.add_node(Node(node_id))
        grafo.add_edge("A", "C")
        grafo.add_edge("B", "C")
        assert grafo.predecessors("C") == frozenset({"A", "B"})
        assert grafo.successors("A") == frozenset({"C"})
        assert grafo.successors("B") == frozenset({"C"})

    def test_vecindad_de_nodo_inexistente_lanza_error(self, grafo):
        with pytest.raises(NodeNotFoundError):
            grafo.successors("Z")
        with pytest.raises(NodeNotFoundError):
            grafo.predecessors("Z")

    def test_la_vecindad_devuelta_no_puede_mutar_el_grafo(self, grafo_abc):
        vecinos = grafo_abc.successors("A")
        assert isinstance(vecinos, frozenset)
        with pytest.raises(AttributeError):
            vecinos.add("Z")  # type: ignore[attr-defined]
        assert grafo_abc.successors("A") == frozenset({"B"})
