class CatalogoError(Exception):
    """Error base del catálogo. Permite capturar todo con un solo except."""


class IdElementoInvalidoError(CatalogoError):
    """El identificador recibido no cumple el formato exigido."""


class TipoElementoInvalidoError(CatalogoError):
    """El tipo no es PRODUCTO, INSUMO ni PROVEEDOR."""

    def __init__(self, valor: object, tipos_validos: tuple[str, ...]) -> None:
        self.valor = valor
        self.tipos_validos = tipos_validos
        super().__init__(
            f"Tipo de elemento inválido: {valor!r}. "
            f"Valores admitidos: {', '.join(tipos_validos)}."
        )


class ElementoNoEncontradoError(CatalogoError):
    """El elemento no está registrado en el catálogo."""

    def __init__(self, id_elemento: str) -> None:
        self.id_elemento = id_elemento
        super().__init__(f"El elemento '{id_elemento}' no existe en el catálogo.")


class ElementoDuplicadoError(CatalogoError):
    """Ya existe un elemento con ese id (sin distinguir mayúsculas)."""

    def __init__(self, id_solicitado: str, id_existente: str) -> None:
        self.id_solicitado = id_solicitado
        self.id_existente = id_existente
        if id_solicitado == id_existente:
            mensaje = f"Ya existe un elemento con el identificador '{id_existente}'."
        else:
            mensaje = (
                f"El identificador '{id_solicitado}' choca con el elemento "
                f"'{id_existente}' ya registrado (los ids no distinguen "
                f"mayúsculas de minúsculas)."
            )
        super().__init__(mensaje)


class DependenciaDuplicadaError(CatalogoError):
    """La dependencia ya estaba registrada."""

    def __init__(self, origen_id: str, destino_id: str) -> None:
        self.origen_id = origen_id
        self.destino_id = destino_id
        super().__init__(
            f"Ya está registrado que '{origen_id}' requiere '{destino_id}'."
        )


class AutodependenciaError(CatalogoError):
    """Un elemento no puede requerirse a sí mismo."""

    def __init__(self, id_elemento: str) -> None:
        self.id_elemento = id_elemento
        super().__init__(
            f"Un elemento no puede requerirse a sí mismo: '{id_elemento}'."
        )
