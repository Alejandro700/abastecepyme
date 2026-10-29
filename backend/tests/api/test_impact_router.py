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
        ("Suelto", "PROVEEDOR"),
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


class TestImpacto:
    def test_un_proveedor_afecta_una_cadena(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/elementos/MaderasDelSur/impacto")

        cuerpo = respuesta.json()
        assert respuesta.status_code == 200
        assert cuerpo["estado"] == "CON_IMPACTO"
        assert cuerpo["sentido"] == "IMPACTO"
        assert cuerpo["total"] == 3
        assert [a["id"] for a in cuerpo["alcanzados"]] == ["Madera", "Mesa", "Silla"]

    def test_cada_elemento_trae_nivel_cadena_y_explicacion(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/MaderasDelSur/impacto").json()

        silla = next(a for a in cuerpo["alcanzados"] if a["id"] == "Silla")
        assert silla["tipo"] == "PRODUCTO"
        assert silla["nivel"] == 2
        assert silla["cadena"] == ["Silla", "Madera", "MaderasDelSur"]
        assert silla["explicacion"] == "Silla requiere Madera, que requiere MaderasDelSur"

    def test_el_mensaje_describe_la_consecuencia(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/MaderasDelSur/impacto").json()

        assert cuerpo["mensaje"] == (
            "Si 'MaderasDelSur' deja de estar disponible, se afectan 3 elementos."
        )

    def test_el_mensaje_usa_singular_con_un_solo_afectado(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/Tornillos/impacto").json()

        assert cuerpo["total"] == 1
        assert "se afecta 1 elemento." in cuerpo["mensaje"]

    def test_elemento_que_nadie_requiere_devuelve_200_sin_impacto(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/elementos/Silla/impacto")

        cuerpo = respuesta.json()
        assert respuesta.status_code == 200
        assert cuerpo["estado"] == "SIN_IMPACTO"
        assert cuerpo["total"] == 0
        assert cuerpo["alcanzados"] == []

    def test_elemento_sin_relaciones_devuelve_200_sin_impacto(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/Suelto/impacto").json()

        assert cuerpo["estado"] == "SIN_IMPACTO"

    def test_elemento_inexistente_devuelve_404(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/elementos/Pata/impacto")

        assert respuesta.status_code == 404
        assert respuesta.json()["error_code"] == "ELEMENTO_NO_ENCONTRADO"
        assert respuesta.json()["details"] == {"id_elemento": "Pata"}

    def test_no_distingue_mayusculas(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/elementos/maderasdelsur/impacto")

        assert respuesta.status_code == 200
        assert respuesta.json()["consultado"]["id"] == "MaderasDelSur"

    def test_catalogo_vacio_devuelve_404(self, cliente):
        assert cliente.get("/api/elementos/Silla/impacto").status_code == 404

    def test_consultar_no_cambia_la_red(self, cliente_cargado):
        antes = cliente_cargado.get("/api/red").json()

        cliente_cargado.get("/api/elementos/MaderasDelSur/impacto")
        cliente_cargado.get("/api/elementos/Silla/requisitos")

        assert cliente_cargado.get("/api/red").json() == antes

    def test_refleja_una_dependencia_registrada_despues(self, cliente_cargado):
        cliente_cargado.post(
            "/api/dependencias", json={"origen_id": "Mesa", "destino_id": "Tornillos"}
        )

        cuerpo = cliente_cargado.get("/api/elementos/Tornillos/impacto").json()

        assert [a["id"] for a in cuerpo["alcanzados"]] == ["Mesa", "Silla"]


class TestRequisitos:
    def test_un_producto_necesita_su_cadena(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/Silla/requisitos").json()

        assert cuerpo["estado"] == "CON_REQUISITOS"
        assert cuerpo["sentido"] == "REQUISITOS"
        assert [a["id"] for a in cuerpo["alcanzados"]] == [
            "Madera",
            "Tornillos",
            "MaderasDelSur",
        ]

    def test_la_cadena_empieza_en_el_elemento_consultado(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/Silla/requisitos").json()

        proveedor = cuerpo["alcanzados"][-1]
        assert proveedor["cadena"] == ["Silla", "Madera", "MaderasDelSur"]
        assert proveedor["explicacion"] == "Silla requiere Madera, que requiere MaderasDelSur"

    def test_un_proveedor_no_requiere_nada(self, cliente_cargado):
        cuerpo = cliente_cargado.get("/api/elementos/MaderasDelSur/requisitos").json()

        assert cuerpo["estado"] == "SIN_REQUISITOS"
        assert cuerpo["alcanzados"] == []

    def test_elemento_inexistente_devuelve_404(self, cliente_cargado):
        respuesta = cliente_cargado.get("/api/elementos/Pata/requisitos")

        assert respuesta.status_code == 404
        assert respuesta.json()["error_code"] == "ELEMENTO_NO_ENCONTRADO"


class TestDocumentacion:
    def test_los_endpoints_aparecen_en_openapi(self, cliente):
        rutas = cliente.get("/openapi.json").json()["paths"]

        assert "/api/elementos/{id_elemento}/impacto" in rutas
        assert "/api/elementos/{id_elemento}/requisitos" in rutas
