from ..graph import (
    CycleError,
    DirectedGraph,
    DuplicateEdgeError,
    DuplicateNodeError,
    EdgeNotFoundError,
    Node,
    Visit,
)
from .alcance import Alcance, ElementoAlcanzado, SentidoConsulta
from .dependencia import Dependencia
from .elemento import Elemento, clave_de, normalizar_id
from .errors import (
    AutodependenciaError,
    CatalogoError,
    CicloDetectadoError,
    DependenciaDuplicadaError,
    DependenciaNoEncontradaError,
    ElementoDuplicadoError,
    ElementoNoEncontradoError,
)
from .produccion import EtapaProduccion, OrdenProduccion


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

    def eliminar_dependencia(self, origen_id: object, destino_id: object) -> None:
        origen = self._resolver(origen_id)
        destino = self._resolver(destino_id)
        try:
            self._grafo.remove_edge(origen.id, destino.id)
        except EdgeNotFoundError:
            raise DependenciaNoEncontradaError(origen.id, destino.id) from None

    def listar_dependencias(self) -> tuple[Dependencia, ...]:
        return tuple(
            Dependencia(origen_id=arista.source_id, destino_id=arista.target_id)
            for arista in self._grafo.edges()
        )

    def total_dependencias(self) -> int:
        return self._grafo.edge_count()

    def impacto_de(self, id_elemento: object) -> Alcance:
        """Qué se afecta si el elemento deja de estar disponible.

        Se afectan quienes lo requieren, directa o indirectamente: se recorre
        la red contra el sentido de las flechas.
        """
        elemento = self._resolver(id_elemento)
        visitas = self._grafo.ancestors(elemento.id)
        return self._armar_alcance(elemento, SentidoConsulta.IMPACTO, visitas)

    def requisitos_de(self, id_elemento: object) -> Alcance:
        """Qué necesita el elemento, directa o indirectamente.

        Se recorre la red a favor del sentido de las flechas.
        """
        elemento = self._resolver(id_elemento)
        visitas = self._grafo.descendants(elemento.id)
        return self._armar_alcance(elemento, SentidoConsulta.REQUISITOS, visitas)

    def orden_de_preparacion(self, id_elemento: object | None = None) -> OrdenProduccion:
        """Orden válido de preparación, o CicloDetectadoError si hay contradicción.

        Cada elemento aparece después de todo lo que requiere. Sin `id_elemento`
        se ordena toda la red; con él, solo lo necesario para ese elemento.
        Nunca se devuelve un orden falso: si hay un ciclo, se levanta el error.
        """
        objetivo = None
        alcance = None
        if id_elemento is not None:
            objetivo = self._resolver(id_elemento)
            necesarios = self._grafo.descendants(objetivo.id)
            alcance = {objetivo.id, *(visita.node_id for visita in necesarios)}

        try:
            capas = self._grafo.build_layers(alcance)
        except CycleError as error:
            raise CicloDetectadoError(error.cycle, error.blocked) from None

        etapas = tuple(
            EtapaProduccion(
                numero=numero,
                elementos=tuple(self._elementos[clave_de(n)] for n in capa),
            )
            for numero, capa in enumerate(capas, start=1)
        )
        return OrdenProduccion(objetivo=objetivo, etapas=etapas)

    def _armar_alcance(
        self,
        consultado: Elemento,
        sentido: SentidoConsulta,
        visitas: tuple[Visit, ...],
    ) -> Alcance:
        alcanzados = []
        for visita in visitas:
            # La cadena siempre se lee a favor de las flechas ("A requiere B").
            # En el impacto el recorrido va al revés, así que se invierte.
            cadena = visita.path
            if sentido is SentidoConsulta.IMPACTO:
                cadena = tuple(reversed(cadena))
            alcanzados.append(
                ElementoAlcanzado(
                    elemento=self._elementos[clave_de(visita.node_id)],
                    nivel=visita.depth,
                    cadena=cadena,
                )
            )
        return Alcance(
            consultado=consultado, sentido=sentido, alcanzados=tuple(alcanzados)
        )

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
