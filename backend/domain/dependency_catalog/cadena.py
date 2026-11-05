def describir_cadena(cadena: tuple[str, ...]) -> str:
    """La cadena en lenguaje natural: 'A requiere B, que requiere C'."""
    primero, *resto = cadena
    return f"{primero} requiere " + ", que requiere ".join(resto)
