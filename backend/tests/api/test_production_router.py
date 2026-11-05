import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_catalog_service
from application import CatalogService
from infrastructure import InMemoryCatalogRepository
from main import app


@pytest.fixture
def cliente() -> TestClient:
    repositorio = InMemoryCatalogRepository()
    app.dependency_overrides[get_catalog_service] = lambda: CatalogService(
        repositorio
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_cargado(cliente) -> TestClient:
    for id_elemento, tipo in [
        ("Silla", "PRODUCTO"),
        ("Mesa", "PRODUCTO"),
        ("Madera", "INSUMO"),
        ("Tornillos", "INSUMO"),
        ("MaderasDelSur", "PROVEEDOR"),
    ]:
        cliente.post("/api/elementos", json={"id": id_elemento, "tipo": tipo})
    for origen, destino in [
        ("Silla", "Madera"),
        ("Silla", "Tornillos"),
        ("Mesa", "Madera"),
        ("Madera", "MaderasDelSur"),
    ]:
        cliente.post(
            "/api/dependencias",
            json={"origen_id": origen, "destino_id": destino},
        )
    return cliente


@pytest.fixture
def cliente_con_ciclo(cliente_cargado) -> TestClient:
    cliente_cargado.post(
        "/api/dependencias",
        json={"origen_id": "MaderasDelSur", "destino_id": "Silla"},
    )
    return cliente_cargado


def _ids(etapas: list[dict]) -> list[list[str]]:
    return [[e["id"] for e in etapa["elementos"]] for etapa in etapas]


class TestAceptacionCasoAciclico:
    """Cadena válida: se entrega un orden de trabajo."""

    def test_devuelve_200_con_el_orden_por_etapas(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/orden")

        assert respuesta.status_code == 200
        assert _ids(respuesta.json()["etapas"]) == [
            ["MaderasDelSur", "Tornillos"],
            ["Madera"],
            ["Mesa", "Silla"],
        ]

    def test_trae_la_secuencia_de_una_sola_linea(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/orden").json()

        assert [e["id"] for e in cuerpo["secuencia"]] == [
            "MaderasDelSur",
            "Tornillos",
            "Madera",
            "Mesa",
            "Silla",
        ]

    def test_cada_elemento_trae_su_tipo(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/orden").json()

        assert cuerpo["etapas"][0]["elementos"][0] == {
            "id": "MaderasDelSur",
            "tipo": "PROVEEDOR",
        }

    def test_trae_totales_y_mensaje(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/orden").json()

        assert cuerpo["total_elementos"] == 5
        assert cuerpo["total_etapas"] == 3
        assert cuerpo["objetivo"] is None
        assert cuerpo["mensaje"] == "Orden de preparación: 5 elementos en 3 etapas."

    def test_las_etapas_vienen_numeradas(self, cliente_cargado):
        etapas = cliente_cargado.get("/api/orden").json()["etapas"]

        assert [etapa["numero"] for etapa in etapas] == [1, 2, 3]


class TestAceptacionCasoCiclico:
    """Dependencias contradictorias: alerta clara y ningún orden falso."""

    def test_devuelve_409_con_el_codigo_de_ciclo(self, cliente_con_ciclo):
        respuesta = cliente_con_ciclo.get("/api/orden")

        assert respuesta.status_code == 409
        assert respuesta.json()["error_code"] == "CICLO_DETECTADO"

    def test_reporta_el_ciclo_concreto(self, cliente_con_ciclo):
        detalles = cliente_con_ciclo.get("/api/orden").json()["details"]

        assert detalles["ciclo"] == ["Madera", "MaderasDelSur", "Silla", "Madera"]
        assert detalles["explicacion"] == (
            "Madera requiere MaderasDelSur, que requiere Silla, que requiere Madera"
        )

    def test_lista_los_elementos_bloqueados(self, cliente_con_ciclo):
        detalles = cliente_con_ciclo.get("/api/orden").json()["details"]

        assert detalles["bloqueados"] == ["Madera", "MaderasDelSur", "Mesa", "Silla"]

    def test_el_mensaje_nombra_el_ciclo(self, cliente_con_ciclo):
        mensaje = cliente_con_ciclo.get("/api/orden").json()["message"]

        assert "ciclo" in mensaje
        assert "Madera requiere MaderasDelSur" in mensaje

    def test_no_devuelve_ningun_orden(self, cliente_con_ciclo):
        cuerpo = cliente_con_ciclo.get("/api/orden").json()

        assert "etapas" not in cuerpo
        assert "secuencia" not in cuerpo

    def test_el_orden_vuelve_al_quitar_la_contradiccion(self, cliente):
        for id_elemento in ("A", "B"):
            cliente.post("/api/elementos", json={"id": id_elemento, "tipo": "INSUMO"})
        cliente.post("/api/dependencias", json={"origen_id": "A", "destino_id": "B"})
        assert cliente.get("/api/orden").status_code == 200

        cliente.post("/api/dependencias", json={"origen_id": "B", "destino_id": "A"})

        assert cliente.get("/api/orden").status_code == 409


class TestOrdenParaProducir:
    def test_solo_incluye_lo_que_el_producto_necesita(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/Silla/orden").json()

        assert _ids(cuerpo["etapas"]) == [["MaderasDelSur", "Tornillos"], ["Madera"], ["Silla"]]
        assert cuerpo["objetivo"] == {"id": "Silla", "tipo": "PRODUCTO"}

    def test_el_mensaje_dice_que_el_producto_va_al_final(self, cliente_cargado):
        mensaje = cliente_cargado.get("/api/elementos/Mesa/orden").json()["mensaje"]

        assert mensaje == (
            "Para producir 'Mesa' hay que preparar 3 elementos en 3 etapas; "
            "'Mesa' va al final."
        )

    def test_no_distingue_mayusculas(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/elementos/silla/orden")

        assert respuesta.status_code == 200
        assert respuesta.json()["objetivo"]["id"] == "Silla"

    def test_elemento_inexistente_devuelve_404(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/elementos/Pata/orden")

        assert respuesta.status_code == 404
        assert respuesta.json()["error_code"] == "ELEMENTO_NO_ENCONTRADO"

    def test_un_ciclo_en_su_cadena_devuelve_409(self, cliente_con_ciclo):
        respuesta = cliente_con_ciclo.get("/api/elementos/Silla/orden")

        assert respuesta.status_code == 409
        assert respuesta.json()["error_code"] == "CICLO_DETECTADO"

    def test_un_ciclo_ajeno_no_lo_bloquea(self, cliente_cargado):
        for id_elemento in ("X", "Y"):
            cliente_cargado.post("/api/elementos", json={"id": id_elemento, "tipo": "INSUMO"})
        for origen, destino in (("X", "Y"), ("Y", "X")):
            cliente_cargado.post(
                "/api/dependencias", json={"origen_id": origen, "destino_id": destino}
            )

        assert cliente_cargado.get("/api/orden").status_code == 409
        assert cliente_cargado.get("/api/elementos/Silla/orden").status_code == 200


class TestCasosBorde:
    def test_catalogo_vacio_devuelve_200_sin_etapas(self, cliente):
        respuesta = cliente.get("/api/orden")

        assert respuesta.status_code == 200
        assert respuesta.json()["etapas"] == []
        assert respuesta.json()["mensaje"] == "No hay elementos que ordenar."

    def test_consultar_no_cambia_la_red(self, cliente_cargado):
        antes = cliente_cargado.get("/api/red").json()

        cliente_cargado.get("/api/orden")
        cliente_cargado.get("/api/elementos/Silla/orden")

        assert cliente_cargado.get("/api/red").json() == antes

    def test_los_endpoints_aparecen_en_openapi(self, cliente):
        rutas = cliente.get("/openapi.json").json()["paths"]

        assert "/api/orden" in rutas
        assert "/api/elementos/{id_elemento}/orden" in rutas
