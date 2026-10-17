"""Mediciones de red (ping) multiplataforma.

Idea clave: no se lee el resumen del ping (cambia con el idioma del sistema).
Se cuentan las respuestas individuales 'time=XX ms' / 'tiempo=XX ms', y de ahí
salen latencia, jitter y pérdida. Funciona igual en Windows (es/en), Linux y macOS.
"""
import logging
import platform
import re
import statistics
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from . import config
from .seguridad import validar_host

log = logging.getLogger("hermes.network")
_RESPUESTA = re.compile(r"(?:time|tiempo)\s*[=<]\s*(\d+(?:[.,]\d+)?)\s*ms?", re.IGNORECASE)


@dataclass
class ResultadoPing:
    host: str
    enviados: int
    tiempos_ms: List[float] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def recibidos(self):
        return len(self.tiempos_ms)

    @property
    def conexion(self):
        return self.recibidos > 0

    @property
    def perdida(self):
        """Porcentaje de paquetes perdidos (100 si no hubo ninguna respuesta)."""
        if self.enviados <= 0:
            return None
        return round(100 * (self.enviados - self.recibidos) / self.enviados, 1)

    @property
    def latencia(self):
        return round(statistics.mean(self.tiempos_ms), 1) if self.tiempos_ms else None

    @property
    def jitter(self):
        """Desviación estándar de los tiempos de respuesta (ms)."""
        if len(self.tiempos_ms) >= 2:
            return round(statistics.pstdev(self.tiempos_ms), 1)
        return 0.0 if self.tiempos_ms else None


def parsear_ping(salida, host, enviados):
    """Convierte la salida de texto de `ping` en un ResultadoPing."""
    tiempos = [float(t.replace(",", ".")) for t in _RESPUESTA.findall(salida)]
    return ResultadoPing(host=host, enviados=enviados, tiempos_ms=tiempos[:enviados])


def _comando_ping(host, cantidad):
    sistema = platform.system()
    if sistema == "Windows":
        return ["ping", "-n", str(cantidad), "-w", "2000", host]
    if sistema == "Darwin":
        return ["ping", "-c", str(cantidad), "-W", "2000", host]
    return ["ping", "-c", str(cantidad), "-W", "2", host]


def hacer_ping(host=None, cantidad=None):
    """Ejecuta ping de forma segura (sin shell, host validado, con timeout)."""
    host = validar_host(host or config.HOST_PRUEBA)
    cantidad = cantidad or config.NUM_PINGS
    try:
        r = subprocess.run(
            _comando_ping(host, cantidad),
            capture_output=True, text=True, errors="replace",
            timeout=cantidad * 3 + 5,
        )
        return parsear_ping(r.stdout, host, cantidad)
    except FileNotFoundError:
        log.error("El comando 'ping' no está disponible en este sistema.")
        return ResultadoPing(host, cantidad, error="ping no disponible")
    except subprocess.TimeoutExpired:
        log.warning("Ping a %s excedió el tiempo máximo.", host)
        return ResultadoPing(host, cantidad, error="tiempo agotado")


@dataclass
class MedicionRed:
    """Resumen de una medición: hacia Internet y hacia el router (gateway)."""
    internet: ResultadoPing
    gateway_ip: Optional[str] = None
    gateway: Optional[ResultadoPing] = None

    @property
    def tiene_gateway(self):
        return self.gateway is not None and self.gateway_ip is not None

    def caracteristicas(self):
        """Vector para el modelo de ML, o None si faltan datos del gateway."""
        if not (self.internet.conexion and self.tiene_gateway and self.gateway.conexion):
            return None
        return {
            "latencia": self.internet.latencia,
            "perdida": self.internet.perdida,
            "jitter": self.internet.jitter,
            "latencia_gateway": self.gateway.latencia,
            "perdida_gateway": self.gateway.perdida,
        }


def medir_red(host=None, cantidad=None, gateway_ip=None):
    """Mide Internet y, si se conoce el gateway, también el router.

    Comparar ambos permite distinguir un problema local (Wi-Fi/router) de
    uno del proveedor.
    """
    internet = hacer_ping(host, cantidad)
    gateway = None
    if gateway_ip:
        gateway = hacer_ping(gateway_ip, cantidad)
    return MedicionRed(internet=internet, gateway_ip=gateway_ip, gateway=gateway)
