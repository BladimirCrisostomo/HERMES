"""Router SIMULADO en memoria, para probar HERMES sin tocar ningún router real.

Sirve para desarrollo, pruebas automáticas y demostraciones: implementa toda la
interfaz RouterController, así se puede ensayar bloquear, limitar y revertir
sin riesgo de dejar la red sin conexión.
"""
import logging

from ..capabilities import CONFIRMADA
from ..interface import RouterController

log = logging.getLogger("hermes.router.simulado")

CLIENTES_DE_EJEMPLO = [
    # Direcciones MAC ficticias (prefijo AA:BB:CC) solo para la demostración.
    {"mac": "AA:BB:CC:00:00:01", "ip": "192.168.100.20", "nombre": "laptop-jose", "consumo_kbps": 1200},
    {"mac": "AA:BB:CC:00:00:02", "ip": "192.168.100.21", "nombre": "celular-v", "consumo_kbps": 300},
    {"mac": "AA:BB:CC:00:00:03", "ip": "192.168.100.22", "nombre": "smart-tv", "consumo_kbps": 8500},
    {"mac": "AA:BB:CC:00:00:04", "ip": "192.168.100.23", "nombre": "consola", "consumo_kbps": 15000},
    {"mac": "AA:BB:CC:00:00:05", "ip": "192.168.100.24", "nombre": "desconocido", "consumo_kbps": 50},
]


class RouterSimulado(RouterController):
    def __init__(self, clientes=None, canal=6):
        base = clientes if clientes is not None else CLIENTES_DE_EJEMPLO
        self._clientes = {c["mac"]: {**c, "bloqueado": False, "limite_kbps": None} for c in base}
        self._canal = canal
        self.conectado = False
        self.reinicios = 0

    # --- lectura -----------------------------------------------------------
    def conectar(self):
        self.conectado = True

    def desconectar(self):
        self.conectado = False

    def obtener_informacion(self):
        return {"fabricante": "SIMULADO", "modelo": "RouterSimulado", "firmware": "demo"}

    def obtener_capacidades(self):
        return {c: CONFIRMADA for c in (
            "obtener_clientes", "cambiar_canal_wifi", "bloquear_cliente",
            "limitar_cliente", "reiniciar")}

    def obtener_clientes(self):
        return [dict(c) for c in self._clientes.values()]

    def obtener_configuracion_wifi(self):
        return {"canal": self._canal}

    # --- acciones ----------------------------------------------------------
    def _cliente(self, mac):
        if mac not in self._clientes:
            raise KeyError(f"Cliente desconocido: {mac}")
        return self._clientes[mac]

    def cambiar_canal(self, canal):
        log.info("[SIMULACIÓN] canal %s -> %s", self._canal, canal)
        self._canal = canal

    def bloquear_cliente(self, mac):
        self._cliente(mac)["bloqueado"] = True
        log.info("[SIMULACIÓN] bloqueado %s", mac)

    def desbloquear_cliente(self, mac):
        self._cliente(mac)["bloqueado"] = False
        log.info("[SIMULACIÓN] desbloqueado %s", mac)

    def limitar_cliente(self, mac, kbps):
        self._cliente(mac)["limite_kbps"] = kbps
        log.info("[SIMULACIÓN] límite %s kbps para %s", kbps, mac)

    def quitar_limite(self, mac):
        self._cliente(mac)["limite_kbps"] = None

    def reiniciar(self):
        self.reinicios += 1
        log.info("[SIMULACIÓN] reinicio del router")
