"""Lógica de la interfaz (consola y web): órdenes en lenguaje natural, sesión con el router.

Se mantiene separada de Streamlit para poder probarla sin navegador.
"""
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from . import config, credenciales, dispositivos, motor, nlp
from .politicas import ACCIONES_AUTOMATICAS, GuardianRouter, Modo, Verificador
from .router.manager import RouterManager
from .router.registro import buscar_routers, conectar_router  # noqa: F401  (buscar_routers se reexporta)
from .seguridad import es_ip_privada, sanitizar_texto

log = logging.getLogger("hermes.asistente")

_MAC = re.compile(r"\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b", re.I)
_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
VERBOS_CANAL = {"cambia", "cambiar", "pon", "poner", "usa", "usar", "configura", "configurar",
                "ajusta", "ajustar", "selecciona", "seleccionar", "cambiame"}
VERBOS_BLOQUEAR = {"bloquea", "bloquear", "bloqueame", "expulsa", "expulsar", "corta", "cortar"}
VERBOS_DESBLOQUEAR = {"desbloquea", "desbloquear", "libera", "liberar", "permite", "permitir"}
RUIDO = {"el", "la", "los", "las", "al", "del", "de", "mi", "que", "por", "favor", "una", "uno", "un",
         "con", "para", "red", "wifi", "dispositivo", "equipo", "aparato", "celular", "telefono",
         "en", "y", "o", "se", "lo", "le", "es", "me", "te", "su", "ese", "esa", "este", "esta"}
GENERICOS_MAS = {"canal", "numero", "automatico", "auto"}


@dataclass
class OrdenRouter:
    accion: Optional[str] = None
    valor: object = None
    descripcion: str = ""
    error: Optional[str] = None


# ------------------------------------------------------------------ interpretar órdenes
def _resolver_dispositivo(original, norm, clientes):
    """(cliente_dict | {'mac': ...}, error). Busca por MAC, IP o nombre."""
    m = _MAC.search(original)
    if m:
        mac = m.group(0).upper().replace("-", ":")
        return next((c for c in clientes if c["mac"] == mac), {"mac": mac, "nombre": None, "ip": None}), None
    m = _IP.search(original)
    if m:
        c = next((c for c in clientes if c.get("ip") == m.group(0)), None)
        return (c, None) if c else (None, f"No hay ningún dispositivo con la IP {m.group(0)}.")
    palabras = {p for p in norm.split() if len(p) >= 2 and p not in RUIDO and p not in GENERICOS_MAS
                and p not in VERBOS_BLOQUEAR | VERBOS_DESBLOQUEAR}
    puntuados = []
    for c in clientes:
        nombre = nlp.normalizar(c.get("nombre") or "")
        if not nombre:
            continue
        puntaje = len(set(nombre.split()) & palabras) + (2 if nombre in norm else 0)
        if puntaje:
            puntuados.append((puntaje, c))
    if not puntuados:
        conocidos = ", ".join(c.get("nombre") or c["mac"] for c in clientes) or "ninguno"
        return None, f"No encontré ese dispositivo. Conozco: {conocidos}."
    mejor = max(p for p, _ in puntuados)
    finalistas = [c for p, c in puntuados if p == mejor]
    if len(finalistas) > 1:
        return None, "¿A cuál te refieres? " + ", ".join(c.get("nombre") or c["mac"] for c in finalistas)
    return finalistas[0], None


def interpretar_orden(texto, clientes=()):
    """Devuelve una OrdenRouter si el texto es una orden para el router; si no, None."""
    original = sanitizar_texto(texto, config.LONGITUD_MAXIMA_CONSULTA).lower()
    norm = nlp.normalizar(original)
    palabras = set(norm.split())

    if "canal" in palabras and palabras & VERBOS_CANAL:
        numeros = re.findall(r"\b(\d{1,2})\b", norm)
        if numeros:
            canal = int(numeros[0])
            if canal > 13:
                return OrdenRouter(error="Los canales Wi-Fi de 2.4 GHz van del 1 al 13.")
            nombre = "automático" if canal == 0 else str(canal)
            return OrdenRouter("cambiar_canal", canal, f"Cambiar el canal Wi-Fi a {nombre}")
        if palabras & {"automatico", "auto"}:
            return OrdenRouter("cambiar_canal", 0, "Poner el canal Wi-Fi en automático")
        return OrdenRouter(error="¿A qué canal? Dime un número (por ejemplo 6) o «automático».")

    desbloquear = bool(palabras & VERBOS_DESBLOQUEAR)
    bloquear = bool(palabras & VERBOS_BLOQUEAR) and not desbloquear
    if desbloquear or bloquear:
        if palabras & {"todos", "todo", "todas"}:
            return OrdenRouter(error="Por seguridad HERMES no bloquea ni desbloquea a todos a la vez.")
        cliente, error = _resolver_dispositivo(original, norm, list(clientes))
        if error:
            return OrdenRouter(error=error)
        nombre = cliente.get("nombre") or cliente["mac"]
        accion = "desbloquear_cliente" if desbloquear else "bloquear_cliente"
        verbo = "Desbloquear" if desbloquear else "Bloquear"
        return OrdenRouter(accion, cliente["mac"], f"{verbo} a {nombre} ({cliente['mac']})")
    return None


# --------------------------------------------------------------------- límite de intentos
class LimitadorIntentos:
    """Evita golpear el login del router con contraseñas erróneas (máx. N seguidas)."""

    def __init__(self, maximo=3, espera=30, reloj=time.monotonic):
        self.maximo, self.espera, self._reloj = maximo, espera, reloj
        self.fallos, self._hasta = 0, 0.0

    def segundos_restantes(self):
        return max(0, int(self._hasta - self._reloj()))

    def puede_intentar(self):
        return self.segundos_restantes() == 0

    def registrar_fallo(self):
        self.fallos += 1
        if self.fallos >= self.maximo:
            self._hasta, self.fallos = self._reloj() + self.espera, 0

    def registrar_exito(self):
        self.fallos, self._hasta = 0, 0.0


# ------------------------------------------------------------------------------ sesión
@dataclass
class SesionRouter:
    router: object
    manager: RouterManager
    guardian: GuardianRouter
    simulado: bool
    ip: str
    protegidos: set = field(default_factory=set)

    @property
    def modo(self):
        return self.guardian.modo

    def clientes(self):
        try:
            return self.router.obtener_clientes()
        except Exception:                      # red caída o sesión vencida
            log.exception("No se pudo leer la lista de clientes")
            return []


class _VerificadorSimulado:
    def antes(self): pass
    def despues(self): return True


def conectar(ip, contrasena="", simulacion=False, modo=Modo.CONFIRMAR):
    """Abre una sesión con el router. Devuelve (SesionRouter | None, error | None, diagnóstico | None)."""
    if simulacion:
        conexion = conectar_router(ip, simulacion=True)
        protegidos, verificador = {"AA:BB:CC:00:00:01"}, _VerificadorSimulado()
    else:
        if not es_ip_privada(ip):
            return None, "Esa IP no es de una red local. HERMES solo administra routers de tu red.", None
        cred = credenciales.Credenciales("admin", contrasena)
        conexion = conectar_router(ip, cred)
        if not conexion["correcto"]:
            diag = None
            huella = conexion.get("huella")
            if huella and not conexion.get("adaptador"):
                servidor = str(huella.get("servidor") or "desconocido")[:40]
                titulo = str(huella.get("titulo") or "sin título")[:40]
                return None, (
                    f"{conexion['error']} En {ip} hay un equipo con servidor «{servidor}» y título «{titulo}». "
                    "Si es el módem de tu proveedor, HERMES no lo administra: conéctate al Wi-Fi o al cable "
                    "de tu Mercusys y pulsa «BUSCAR MI ROUTER»."), None
            if conexion.get("adaptador") == "mercusys_mw306r":
                # Pasos del único intento de login (códigos y longitudes, sin secretos).
                diag = dict(getattr(conexion.get("router"), "pasos_login", {}) or {}) or None
            return None, conexion["error"], diag
        try:
            protegidos = dispositivos.macs_protegidas(dispositivos.escanear(gateway=ip))
        except Exception:
            log.exception("No se pudieron calcular los dispositivos protegidos")
            protegidos = set()
        mac_router = conexion["router"].obtener_informacion().get("mac_router")
        if mac_router:
            protegidos.add(mac_router)
        verificador = Verificador(gateway_ip=ip, host=config.HOST_PRUEBA)

    if not conexion["correcto"]:
        return None, conexion["error"], None
    manager = RouterManager()
    manager.establecer_router(conexion["router"])
    guardian = GuardianRouter(manager, modo, protegidos=protegidos, verificador=verificador)
    return SesionRouter(conexion["router"], manager, guardian, simulacion, ip, protegidos), None, None


def requiere_confirmacion(sesion, accion):
    """¿Hace falta que el usuario pulse 'confirmar' antes de ejecutar?"""
    if sesion.modo is Modo.SUGERIR:
        return False                      # no ejecuta nada: solo propone
    return not (sesion.modo is Modo.AUTOMATICO and accion in ACCIONES_AUTOMATICAS)


def ejecutar(sesion, accion, valor, confirmado=False):
    return sesion.guardian.ejecutar(accion, valor, confirmar=lambda texto: confirmado)


# ------------------------------------------------------------------------- conversación
@dataclass
class Turno:
    rol: str                                   # "usuario" | "hermes"
    texto: str = ""
    respuesta: Optional[motor.Respuesta] = None
    orden: Optional[OrdenRouter] = None
    clientes: Optional[list] = None


def atender(texto, sesion=None):
    """Procesa lo que escribió el usuario y devuelve el Turno de HERMES."""
    texto = sanitizar_texto(texto, config.LONGITUD_MAXIMA_CONSULTA)
    if not texto:
        return Turno("hermes", "No recibí ninguna consulta.")
    orden = interpretar_orden(texto, sesion.clientes() if sesion else ())
    if orden is not None:
        if sesion is None:
            return Turno("hermes", "Para eso necesito conexión con el router. "
                                   "Conéctalo en el panel lateral (o activa la simulación).")
        if orden.error:
            return Turno("hermes", orden.error)
        return Turno("hermes", orden.descripcion, orden=orden)
    if sesion is not None and nlp.identificar_intencion(texto) == "listar_dispositivos":
        clientes = sesion.clientes()
        return Turno("hermes", f"El router reporta {len(clientes)} dispositivos conectados.",
                     clientes=clientes)
    respuesta = motor.procesar_consulta(texto)
    texto_respuesta = respuesta.mensaje or ("Análisis de red completado." if respuesta.medicion else "")
    return Turno("hermes", texto_respuesta, respuesta=respuesta)
