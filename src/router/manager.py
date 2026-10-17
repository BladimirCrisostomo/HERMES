"""Administra el adaptador de router en uso y controla las acciones que modifican."""
import logging

from ..seguridad import validar_mac
from .capabilities import CONFIRMADA
from .interface import RouterController

log = logging.getLogger("hermes.router")

LIMITE_MIN_KBPS = 64
LIMITE_MAX_KBPS = 1_000_000


def _validar_canal(canal):
    if isinstance(canal, bool) or not isinstance(canal, int) or not 1 <= canal <= 13:
        raise ValueError("El canal Wi-Fi debe ser un entero entre 1 y 13.")
    return canal


def _validar_limite(valor):
    try:
        mac, kbps = valor
    except (TypeError, ValueError):
        raise ValueError("El límite debe indicarse como (mac, kbps).") from None
    if isinstance(kbps, bool) or not isinstance(kbps, int) or not LIMITE_MIN_KBPS <= kbps <= LIMITE_MAX_KBPS:
        raise ValueError(f"El límite debe ser un entero entre {LIMITE_MIN_KBPS} y {LIMITE_MAX_KBPS} kbps.")
    return (validar_mac(mac), kbps)


def _sin_valor(valor):
    if valor is not None:
        raise ValueError("Esta acción no lleva valor.")
    return None


# acción -> (validador, capacidad requerida)
ACCIONES = {
    "cambiar_canal": (_validar_canal, "cambiar_canal_wifi"),
    "bloquear_cliente": (validar_mac, "bloquear_cliente"),
    "desbloquear_cliente": (validar_mac, "bloquear_cliente"),
    "limitar_cliente": (_validar_limite, "limitar_cliente"),
    "quitar_limite": (validar_mac, "limitar_cliente"),
    "reiniciar": (_sin_valor, "reiniciar"),
}


class RouterManager:
    def __init__(self):
        self.router = None
        self.capacidades = {}

    def establecer_router(self, router, capacidades=None):
        """Si no se indican capacidades, se toman las que declara el propio adaptador."""
        self.router = router
        if capacidades is None and router is not None:
            capacidades = router.obtener_capacidades()
        self.capacidades = capacidades or {}

    def obtener_router(self):
        return self.router

    def conectado(self):
        return self.router is not None

    def consultar_interfaz(self, ruta="/"):
        if self.router is None:
            return {"correcto": False, "error": "No hay ningún adaptador registrado."}
        if not hasattr(self.router, "consultar"):
            return {"correcto": False, "error": "El adaptador no implementa consultas HTTP."}
        return self.router.consultar(ruta)

    @staticmethod
    def validar(accion, valor):
        """Valida y normaliza el valor de una acción (lanza ValueError si no sirve)."""
        if accion not in ACCIONES:
            raise ValueError(f"Acción no permitida: {accion!r}")
        return ACCIONES[accion][0](valor)

    def ejecutar_accion(self, accion, valor, confirmar):
        """Única puerta de entrada para modificar el router.

        `confirmar` es una función(texto) -> bool que pregunta al usuario.
        Sin confirmación explícita, o sin capacidad confirmada, no se hace nada.
        """
        valor = self.validar(accion, valor)
        if not isinstance(self.router, RouterController):
            return {"correcto": False, "error": "El adaptador actual es de solo lectura."}

        capacidad = ACCIONES[accion][1]
        if self.capacidades.get(capacidad) != CONFIRMADA:
            return {"correcto": False,
                    "error": f"La capacidad '{capacidad}' no está confirmada en este router."}

        descripcion = f"{accion}" + ("" if valor is None else f" con valor {valor}")
        if not confirmar(f"¿Confirmas ejecutar {descripcion}?"):
            log.info("Acción %s cancelada por el usuario.", descripcion)
            return {"correcto": False, "error": "Cancelada por el usuario."}

        log.warning("Ejecutando acción %s en el router.", descripcion)
        metodo = getattr(self.router, accion)
        if valor is None:
            metodo()
        elif isinstance(valor, tuple):
            metodo(*valor)
        else:
            metodo(valor)
        return {"correcto": True}
