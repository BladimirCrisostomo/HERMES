"""Guardián de acciones sobre el router: modos, protecciones, verificación y reversión.

Toda acción que MODIFIQUE el router debe pasar por GuardianRouter.ejecutar():

  1. Valida el valor y rechaza objetivos protegidos (este equipo, el propio router).
  2. Aplica un límite de cambios por hora (evita bucles de cambios).
  3. Según el modo:
       SUGERIR     -> solo describe lo que haría; no ejecuta nada.
       CONFIRMAR   -> pregunta al usuario antes de ejecutar.
       AUTOMATICO  -> ejecuta sin preguntar SOLO acciones de bajo riesgo
                      (cambiar canal, limitar/quitar límite). Bloquear y reiniciar
                      siempre piden confirmación.
  4. Guarda el estado previo, ejecuta, y comprueba que la red sigue funcionando.
     Si la verificación falla, REVIERTE el cambio automáticamente.
  5. Registra cada decisión en el log.
"""
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

log = logging.getLogger("hermes.politicas")


class Modo(str, Enum):
    SUGERIR = "sugerir"
    CONFIRMAR = "confirmar"
    AUTOMATICO = "automatico"


ACCIONES_AUTOMATICAS = {"cambiar_canal", "limitar_cliente", "quitar_limite"}
ACCIONES_CON_REVERSION = {
    "cambiar_canal", "bloquear_cliente", "desbloquear_cliente", "limitar_cliente", "quitar_limite",
}


@dataclass
class Resultado:
    ejecutada: bool
    motivo: str
    revertida: bool = False
    plan: str = ""


class Verificador:
    """Comprueba que la red sigue funcionando tras un cambio.

    Interfaz: antes() se llama antes de actuar (toma la línea base) y
    despues() -> bool dice si todo sigue bien. Se puede sustituir en pruebas.
    """

    def __init__(self, gateway_ip=None, host=None):
        self.gateway_ip, self.host = gateway_ip, host
        self._internet_antes = True

    def antes(self):
        from . import network
        self._internet_antes = network.hacer_ping(self.host, 2).conexion

    def despues(self):
        from . import network
        if self.gateway_ip and not network.hacer_ping(self.gateway_ip, 2).conexion:
            return False
        # Si antes había Internet, debe seguir habiéndolo.
        return network.hacer_ping(self.host, 2).conexion or not self._internet_antes


class GuardianRouter:
    def __init__(self, manager, modo=Modo.CONFIRMAR, protegidos=(), verificador=None,
                 max_cambios_por_hora=4, espera_verificacion=60, intervalo=5,
                 reloj=time.monotonic, dormir=time.sleep):
        self.manager = manager
        self.modo = Modo(modo)
        self.protegidos = {p.upper() for p in protegidos}
        self.verificador = verificador
        self.max_cambios_por_hora = max_cambios_por_hora
        self.espera_verificacion = espera_verificacion
        self.intervalo = intervalo
        self._reloj, self._dormir = reloj, dormir
        self._cambios = []   # instantes de los cambios realizados

    # --- ayudas --------------------------------------------------------------
    def _mac_objetivo(self, accion, valor):
        if accion in ("bloquear_cliente", "desbloquear_cliente", "quitar_limite"):
            return valor
        if accion == "limitar_cliente":
            return valor[0]
        return None

    def _cliente(self, mac):
        try:
            return next((c for c in self.manager.router.obtener_clientes() if c["mac"] == mac), None)
        except Exception:
            return None

    def _inversa(self, accion, valor):
        """(acción, valor) que deshace `accion`, o None si no se puede deshacer."""
        router = self.manager.router
        if accion == "cambiar_canal":
            previo = router.obtener_configuracion_wifi().get("canal")
            return ("cambiar_canal", previo) if isinstance(previo, int) else None
        if accion == "bloquear_cliente":
            return ("desbloquear_cliente", valor)
        if accion == "desbloquear_cliente":
            return ("bloquear_cliente", valor)
        mac = self._mac_objetivo(accion, valor)
        cliente = self._cliente(mac) or {}
        previo = cliente.get("limite_kbps")
        if accion == "limitar_cliente":
            return ("quitar_limite", mac) if previo is None else ("limitar_cliente", (mac, previo))
        if accion == "quitar_limite":
            return ("limitar_cliente", (mac, previo)) if previo else None
        return None

    def _limite_de_frecuencia_alcanzado(self):
        ahora = self._reloj()
        self._cambios = [t for t in self._cambios if ahora - t < 3600]
        return len(self._cambios) >= self.max_cambios_por_hora

    def _revisar_proteccion(self, accion, valor):
        mac = self._mac_objetivo(accion, valor)
        if mac and accion != "desbloquear_cliente" and mac in self.protegidos:
            return "Ese dispositivo está protegido (es este equipo o el propio router)."
        if accion == "bloquear_cliente":
            try:
                clientes = self.manager.router.obtener_clientes()
            except Exception:
                clientes = []
            bloqueados = sum(1 for c in clientes if c.get("bloqueado"))
            if clientes and (bloqueados + 1) * 2 >= len(clientes):
                return "Bloquear a este dispositivo dejaría bloqueada a la mitad o más de la red."
        return None

    # --- punto de entrada -----------------------------------------------------
    def ejecutar(self, accion, valor=None, confirmar=lambda texto: False):
        valor = self.manager.validar(accion, valor)
        plan = f"{accion}" + ("" if valor is None else f" {valor}")

        motivo = self._revisar_proteccion(accion, valor)
        if motivo:
            log.warning("Rechazada %s: %s", plan, motivo)
            return Resultado(False, motivo, plan=plan)
        if self._limite_de_frecuencia_alcanzado():
            motivo = f"Límite de {self.max_cambios_por_hora} cambios por hora alcanzado."
            log.warning("Rechazada %s: %s", plan, motivo)
            return Resultado(False, motivo, plan=plan)
        if self.modo is Modo.SUGERIR:
            return Resultado(False, "Modo sugerir: no se ejecutó nada.", plan=plan)

        # En modo automático solo las acciones de bajo riesgo se saltan la pregunta.
        sin_preguntar = self.modo is Modo.AUTOMATICO and accion in ACCIONES_AUTOMATICAS
        if self.modo is Modo.AUTOMATICO and not sin_preguntar:
            log.info("%s no es automática: se pide confirmación.", accion)
        decidir = (lambda texto: True) if sin_preguntar else confirmar

        inversa = self._inversa(accion, valor) if accion in ACCIONES_CON_REVERSION else None
        if self.verificador:
            self.verificador.antes()

        resultado = self.manager.ejecutar_accion(accion, valor, decidir)
        if not resultado["correcto"]:
            return Resultado(False, resultado["error"], plan=plan)
        self._cambios.append(self._reloj())
        log.warning("Acción ejecutada: %s (modo %s)", plan, self.modo.value)

        if self.verificador and accion in ACCIONES_CON_REVERSION:
            if not self._esperar_red_sana():
                return self._revertir(plan, inversa)
        return Resultado(True, "Acción ejecutada y red verificada.", plan=plan)

    def _esperar_red_sana(self):
        limite = self._reloj() + self.espera_verificacion
        while True:
            if self.verificador.despues():
                return True
            if self._reloj() >= limite:
                return False
            self._dormir(self.intervalo)

    def _revertir(self, plan, inversa):
        if inversa is None:
            log.error("La red falló tras %s y NO hay forma automática de revertir.", plan)
            return Resultado(True, "ATENCIÓN: la red no responde y no se pudo revertir automáticamente.",
                             plan=plan)
        accion, valor = inversa
        log.error("La red falló tras %s: revirtiendo con %s.", plan, accion)
        r = self.manager.ejecutar_accion(accion, valor, lambda texto: True)
        if r["correcto"]:
            return Resultado(True, "La red dejó de responder; el cambio se revirtió.", revertida=True, plan=plan)
        return Resultado(True, f"La red falló y la reversión también: {r['error']}", plan=plan)
