#Este archivo será el encargado de administrar qué router está utilizando HERMES.

class RouterManager:#Administra el adaptador seleccionado para un router.

    def __init__(self):
        self.router = None

    def establecer_router(self, router): # Registra un adaptador compatible.
        self.router = router

    def obtener_router(self):
        """
        Devuelve el adaptador registrado.
        """
        return self.router

    def conectado(self):
        """
        Comprueba si existe un adaptador registrado.
        """
        return self.router is not None

    def consultar_interfaz(self, ruta="/"):
        """
        Consulta la interfaz si el adaptador admite HTTP.
        """

        if self.router is None:
            return {
                "correcto": False,
                "error": "No hay ningún adaptador registrado."
            }

        if not hasattr(self.router, "consultar"):
            return {
                "correcto": False,
                "error": (
                    "El adaptador no implementa consultas HTTP."
                )
            }

        return self.router.consultar(ruta)
