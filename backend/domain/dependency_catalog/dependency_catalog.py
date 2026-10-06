from ..graph import (
    DirectedGraph,
    DuplicateEdgeError,
    DuplicateNodeError,
    Node,
)
from .dependencia import Dependencia
from .elemento import Elemento, clave_de, normalizar_id
from .errors import (
    AutodependenciaError,
    CatalogoError,
    DependenciaDuplicadaError,
    ElementoDuplicadoError,
    ElementoNoEncontradoError,
)


class DependencyCatalog:
    """Catálogo de elementos y de las dependencias entre ellos."""

    def __init__(self) -> None:
        # El grafo guarda la topología; el dict, los datos de negocio indexados
        # por clave (sin distinguir mayúsculas) y en orden de alta.
        self._grafo = DirectedGraph()
        self._elementos: dict[str, Elemento] = {}

    def registrar_elemento(self, id_elemento: object, tipo: object) -> Elemento:
        elemento = Elemento.crear(id_elemento, tipo)

        existente = self._elementos.get(elemento.clave)
        if existente is not None:
            raise ElementoDuplicadoError(elemento.id, existente.id)

        # Primero el grafo: si falla, el índice no queda desincronizado.
        try:
            self._grafo.add_node(Node(elemento.id))
        except DuplicateNodeError:
            # Solo ocurriría si grafo e índice se desincronizan.
            raise ElementoDuplicadoError(elemento.id, elemento.id) from None

        self._elementos[elemento.clave] = elemento
        return elemento

    def obtener_elemento(self, id_elemento: object) -> Elemento:
        return self._resolver(id_elemento)

    def existe_elemento(self, id_elemento: object) -> bool:
        try:
            self._resolver(id_elemento)
        except CatalogoError:
            return False
        return True

    def listar_elementos(self) -> tuple[Elemento, ...]:
        return tuple(self._elementos.values())

    def total_elementos(self) -> int:
        return len(self._elementos)

    def registrar_dependencia(
        self, origen_id: object, destino_id: object
    ) -> Dependencia:
        origen = self._resolver(origen_id)
        destino = self._resolver(destino_id)

        # Se compara por clave: 'Madera' y 'madera' son el mismo elemento.
        if origen.clave == destino.clave:
            raise AutodependenciaError(origen.id)

        try:
            self._grafo.add_edge(origen.id, destino.id)
        except DuplicateEdgeError:
            raise DependenciaDuplicadaError(origen.id, destino.id) from None

        return Dependencia(origen_id=origen.id, destino_id=destino.id)

    def listar_dependencias(self) -> tuple[Dependencia, ...]:
        return tuple(
            Dependencia(origen_id=arista.source_id, destino_id=arista.target_id)
            for arista in self._grafo.edges()
        )

    def total_dependencias(self) -> int:
        return self._grafo.edge_count()

    def _resolver(self, id_elemento: object) -> Elemento:
        limpio = normalizar_id(id_elemento)
        elemento = self._elementos.get(clave_de(limpio))
        if elemento is None:
            raise ElementoNoEncontradoError(limpio)
        return elemento

    def __repr__(self) -> str:
        return (
            f"DependencyCatalog(elementos={self.total_elementos()}, "
            f"dependencias={self.total_dependencias()})"
        )
