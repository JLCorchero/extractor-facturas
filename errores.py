class ErrorExtraccion(Exception):
    """Error pensado para eseñarselo a una persona.
    Lleva un código estable (para que el programa decida qué hacer) y un mensaje claro(para el usuario)."""

    def __init__(self, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje