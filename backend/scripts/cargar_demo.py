"""Carga datos sintéticos de demostración en la API que ya está corriendo.

Uso (con el backend levantado, desde la carpeta `backend`):

    python scripts/cargar_demo.py
    python scripts/cargar_demo.py http://localhost:8000

Se puede ejecutar varias veces: lo que ya existe se informa y se omite.
"""

import sys

import httpx

URL_BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

ELEMENTOS = [
    ("Silla", "PRODUCTO"),
    ("Mesa", "PRODUCTO"),
    ("Madera", "INSUMO"),
    ("Tornillos", "INSUMO"),
    ("Barniz", "INSUMO"),
    ("MaderasDelSur", "PROVEEDOR"),
    ("FerreteriaCentral", "PROVEEDOR"),
    ("QuimicosAndinos", "PROVEEDOR"),
]

# (origen, destino) se lee: "Para producir/preparar origen necesito destino".
DEPENDENCIAS = [
    ("Silla", "Madera"),
    ("Silla", "Tornillos"),
    ("Mesa", "Madera"),
    ("Mesa", "Tornillos"),
    ("Mesa", "Barniz"),
    ("Madera", "MaderasDelSur"),
    ("Tornillos", "FerreteriaCentral"),
]

# Se deja sin cargar a propósito para registrarla en vivo durante la demo.
PENDIENTE_EN_VIVO = ("Barniz", "QuimicosAndinos")


def enviar(cliente: httpx.Client, ruta: str, cuerpo: dict, etiqueta: str) -> None:
    respuesta = cliente.post(ruta, json=cuerpo)
    if respuesta.status_code == 201:
        print(f"  creado   {etiqueta}")
    elif respuesta.status_code == 409:
        print(f"  ya existe {etiqueta}")
    else:
        print(f"  ERROR {respuesta.status_code} en {etiqueta}: {respuesta.text}")
        sys.exit(1)


def main() -> None:
    try:
        with httpx.Client(base_url=URL_BASE, timeout=10) as cliente:
            print("Elementos:")
            for id_elemento, tipo in ELEMENTOS:
                enviar(cliente, "/api/elementos", {"id": id_elemento, "tipo": tipo},
                       f"{tipo}: {id_elemento}")

            print("Dependencias:")
            for origen, destino in DEPENDENCIAS:
                enviar(cliente, "/api/dependencias",
                       {"origen_id": origen, "destino_id": destino},
                       f"{origen} requiere {destino}")

            red = cliente.get("/api/red").json()
    except httpx.ConnectError:
        print(f"No se pudo conectar con {URL_BASE}. ¿Está corriendo el backend?")
        sys.exit(1)

    print(
        f"\nListo: {red['total_elementos']} elementos y "
        f"{red['total_dependencias']} dependencias en el catálogo."
    )
    print(
        "Para registrar en vivo en la demo: "
        f"{PENDIENTE_EN_VIVO[0]} requiere {PENDIENTE_EN_VIVO[1]}."
    )


if __name__ == "__main__":
    main()
