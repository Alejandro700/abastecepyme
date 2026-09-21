

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import catalog_router, registrar_manejadores

ORIGENES_PERMITIDOS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app = FastAPI(
    title="AbastecePyme — API de dependencias",
    version="1.0.0",
    description=(
        "Catálogo de dependencias entre productos, insumos y proveedores.\n\n"
        "**Dirección de la arista:** `origen → destino` significa que el "
        "origen REQUIERE al destino. Ejemplo: Silla → Madera se lee "
        "'para producir Silla necesito Madera'."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores(app)
app.include_router(catalog_router)


@app.get("/health", tags=["sistema"], summary="Verificar que la API responde")
def health() -> dict:
    return {"status": "ok"}
