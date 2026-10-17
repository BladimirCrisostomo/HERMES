"""Selecciona un adaptador de router según los servicios detectados."""
from .adapters.generic_http import GenericHTTPAdapter
from .detector import RouterDetector


class RouterAdapterFactory:
    """Por ahora solo existen adaptadores HTTP de lectura."""

    def __init__(self, ip):
        self.ip = ip
        self.detector = RouterDetector(ip)

    def crear_adaptador(self):
        servicios = self.detector.detectar_servicios()
        if servicios.get("http"):
            return {
                "adaptador": GenericHTTPAdapter(self.ip), "tipo": "http",
                "servicios": servicios,
                "motivo": "Se detectó HTTP: se eligió el adaptador HTTP de lectura.",
            }
        return {
            "adaptador": None, "tipo": None, "servicios": servicios,
            "motivo": "No hay servicio compatible con los adaptadores implementados.",
        }
