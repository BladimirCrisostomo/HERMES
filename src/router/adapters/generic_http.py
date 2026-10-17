"""Adaptador genérico de SOLO LECTURA para interfaces HTTP de routers."""
from .. import http_client


class GenericHTTPAdapter:
    """No inicia sesión ni modifica la configuración del router."""

    def __init__(self, ip, timeout=3):
        self.ip = ip
        self.timeout = timeout

    def consultar(self, ruta="/"):
        r = http_client.obtener(self.ip, ruta, "http", self.timeout)
        r.pop("cuerpo", None)   # el adaptador solo expone metadatos
        return r
