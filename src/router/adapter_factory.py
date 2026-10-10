
from detector import RouterDetector
from adapters.generic_http import GenericHTTPAdapter


class RouterAdapterFactory:
    """
    Selecciona un adaptador según los servicios detectados.

    Por ahora solo crea adaptadores HTTP de lectura.
    """

    def __init__(self, ip):
        self.ip = ip
        self.detector = RouterDetector(ip)

    def crear_adaptador(self):
        """
        Detecta los servicios y selecciona un adaptador.
        """

        servicios = self.detector.detectar_servicios()

        # Si HTTP responde, podemos probar el adaptador HTTP.
        if servicios.get("http"):
            return {
                "adaptador": GenericHTTPAdapter(self.ip),
                "tipo": "http",
                "servicios": servicios,
                "motivo": (
                    "Se detectó el puerto HTTP. "
                    "Se seleccionó el adaptador HTTP de lectura."
                )
            }

        # Todavía no tenemos un adaptador SSH ni una API
        # implementados. No fingimos que existen.
        return {
            "adaptador": None,
            "tipo": None,
            "servicios": servicios,
            "motivo": (
                "No se detectó un servicio compatible "
                "con los adaptadores implementados."
            )
        }
