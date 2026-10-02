#Este archivo será el encargado de administrar qué router está utilizando HERMES.
class RouterManager:#esto es un singleton que mantiene la instancia del router actual

    def __init__(self):
        self.router = None

    def establecer_router(self, router):
        self.router = router

    def obtener_router(self):
        return self.router

    def conectado(self):
        return self.router is not None