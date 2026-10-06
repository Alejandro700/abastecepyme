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
    # `app` es compartido por todos los tests: se limpian los overrides.
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_cargado(cliente) -> TestClient:
    for id_elemento, tipo in [
        ("Silla", "PRODUCTO"),
        ("Madera", "INSUMO"),
        ("Tornillos", "INSUMO"),
        ("MaderasDelSur", "PROVEEDOR"),
    ]:
        cliente.post("/api/elementos", json={"id": id_elemento, "tipo": tipo})
    for origen, destino in [
        ("Silla", "Madera"),
        ("Silla", "Tornillos"),
        ("Madera", "MaderasDelSur"),
    ]:
        cliente.post(
            "/api/dependencias",
            json={"origen_id": origen, "destino_id": destino},
        )
    return cliente


class TestSistema:
    def test_health_responde(self, cliente):
        respuesta = cliente.get("/health")
        assert respuesta.status_code == 200
        assert respuesta.json() == {"status": "ok"}

    def test_la_documentacion_se_genera(self, cliente):
        assert cliente.get("/openapi.json").status_code == 200


class TestCrearElemento:
    def test_devuelve_201_y_el_elemento(self, cliente):
        respuesta = cliente.post(
            "/api/elementos", json={"id": "Silla", "tipo": "PRODUCTO"}
        )
        assert respuesta.status_code == 201
        assert respuesta.json() == {"id": "Silla", "tipo": "PRODUCTO"}

    @pytest.mark.parametrize("tipo", ["producto", "  Producto  ", "PRODUCTO"])
    def test_acepta_el_tipo_escrito_de_cualquier_forma(self, cliente, tipo):
        respuesta = cliente.post("/api/elementos", json={"id": "Silla", "tipo": tipo})
        assert respuesta.status_code == 201
        assert respuesta.json()["tipo"] == "PRODUCTO"

    def test_normaliza_el_id(self, cliente):
        respuesta = cliente.post(
            "/api/elementos", json={"id": "  Silla  ", "tipo": "PRODUCTO"}
        )
        assert respuesta.json()["id"] == "Silla"

    def test_duplicado_devuelve_409(self, cliente):
        cliente.post("/api/elementos", json={"id": "Silla", "tipo": "PRODUCTO"})
        respuesta = cliente.post(
            "/api/elementos", json={"id": "silla", "tipo": "PRODUCTO"}
        )
        assert respuesta.status_code == 409
        assert respuesta.json()["error_code"] == "ELEMENTO_DUPLICADO"

    def test_tipo_invalido_devuelve_422(self, cliente):
        respuesta = cliente.post(
            "/api/elementos", json={"id": "Mesa", "tipo": "MUEBLE"}
        )
        assert respuesta.status_code == 422
        assert respuesta.json()["error_code"] == "TIPO_INVALIDO"

    def test_falta_un_campo_devuelve_422_con_el_mismo_contrato(self, cliente):
        respuesta = cliente.post("/api/elementos", json={"id": "Silla"})
        assert respuesta.status_code == 422
        cuerpo = respuesta.json()
        assert cuerpo["error_code"] == "CUERPO_INVALIDO"
        assert set(cuerpo) == {"error_code", "message", "details"}


class TestListarElementos:
    def test_catalogo_vacio_devuelve_200_con_lista_vacia(self, cliente):
        respuesta = cliente.get("/api/elementos")
        assert respuesta.status_code == 200
        assert respuesta.json() == []

    def test_lista_en_orden_de_alta(self, cliente_cargado):
        ids = [e["id"] for e in cliente_cargado.get("/api/elementos").json()]
        assert ids == ["Silla", "Madera", "Tornillos", "MaderasDelSur"]


class TestCrearDependencia:
    def test_devuelve_201_con_la_frase(self, cliente_cargado):
        respuesta = cliente_cargado.post(
            "/api/dependencias",
            json={"origen_id": "Silla", "destino_id": "MaderasDelSur"},
        )
        assert respuesta.status_code == 201
        cuerpo = respuesta.json()
        assert cuerpo["origen_id"] == "Silla"
        assert cuerpo["frase"] == (
            "Para producir/preparar Silla necesito MaderasDelSur"
        )

    def test_elemento_inexistente_devuelve_404(self, cliente_cargado):
        respuesta = cliente_cargado.post(
            "/api/dependencias", json={"origen_id": "Mesa", "destino_id": "Madera"}
        )
        assert respuesta.status_code == 404
        assert respuesta.json()["error_code"] == "ELEMENTO_NO_ENCONTRADO"

    def test_dependencia_repetida_devuelve_409(self, cliente_cargado):
        respuesta = cliente_cargado.post(
            "/api/dependencias", json={"origen_id": "Silla", "destino_id": "Madera"}
        )
        assert respuesta.status_code == 409
        assert respuesta.json()["error_code"] == "DEPENDENCIA_DUPLICADA"

    def test_autodependencia_devuelve_422(self, cliente_cargado):
        respuesta = cliente_cargado.post(
            "/api/dependencias", json={"origen_id": "Silla", "destino_id": "Silla"}
        )
        assert respuesta.status_code == 422
        assert respuesta.json()["error_code"] == "AUTODEPENDENCIA"

    def test_el_error_trae_detalles_utiles(self, cliente_cargado):
        respuesta = cliente_cargado.post(
            "/api/dependencias", json={"origen_id": "Mesa", "destino_id": "Madera"}
        )
        assert respuesta.json()["details"]["id_elemento"] == "Mesa"


class TestListarDependencias:
    def test_sin_dependencias_devuelve_lista_vacia(self, cliente):
        assert cliente.get("/api/dependencias").json() == []

    def test_lista_en_orden_estable(self, cliente_cargado):
        pares = [
            (d["origen_id"], d["destino_id"])
            for d in cliente_cargado.get("/api/dependencias").json()
        ]
        assert pares == [
            ("Silla", "Madera"),
            ("Silla", "Tornillos"),
            ("Madera", "MaderasDelSur"),
        ]


class TestRed:
    def test_devuelve_la_red_completa(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/red").json()
        assert cuerpo["total_elementos"] == 4
        assert cuerpo["total_dependencias"] == 3

    def test_la_red_es_consistente(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/red").json()
        ids = {e["id"] for e in cuerpo["elementos"]}
        for dependencia in cuerpo["dependencias"]:
            assert dependencia["origen_id"] in ids
            assert dependencia["destino_id"] in ids

    def test_red_vacia(self, cliente):
        cuerpo = cliente.get("/api/red").json()
        assert cuerpo == {
            "elementos": [],
            "dependencias": [],
            "total_elementos": 0,
            "total_dependencias": 0,
        }


class TestAislamiento:
    def test_cada_test_arranca_con_catalogo_limpio(self, cliente):
        assert cliente.get("/api/elementos").json() == []
