"""Detecta servicios de administración en el router (puertos TCP)."""
import socket
from concurrent.futures import ThreadPoolExecutor

from ..seguridad import exigir_ip_privada

PUERTOS = {"http": 80, "https": 443, "ssh": 22}


class RouterDetector:
    def __init__(self, ip):
        # Solo se sondean equipos de la red local.
        self.ip = exigir_ip_privada(ip)

    def comprobar_puerto(self, puerto, timeout=1):
        try:
            with socket.create_connection((self.ip, puerto), timeout=timeout):
                return True
        except OSError:
            return False

    def detectar_servicios(self):
        """Comprueba los puertos en paralelo (antes: uno tras otro, hasta 3 s)."""
        with ThreadPoolExecutor(max_workers=len(PUERTOS)) as pool:
            futuros = {n: pool.submit(self.comprobar_puerto, p) for n, p in PUERTOS.items()}
            return {nombre: f.result() for nombre, f in futuros.items()}

    def analizar(self):
        return {"ip": self.ip, "servicios": self.detectar_servicios()}
