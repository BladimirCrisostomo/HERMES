"""Descubrimiento de la red local: nombre del equipo, IP local y gateway.

Funciona en Windows, Linux y macOS. El análisis del texto de cada comando está
en funciones puras (parsear_*) para poder probarlas sin tocar la red.
"""
import ipaddress
import logging
import platform
import re
import socket
import subprocess

log = logging.getLogger("hermes.discovery")
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def obtener_nombre_equipo():
    return socket.gethostname()


def obtener_ip_local():
    """IP de la interfaz que usaría el equipo para salir a Internet.

    No envía datos: un socket UDP 'conectado' solo le pregunta al sistema
    qué interfaz usaría. Es más fiable que gethostbyname(hostname).
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def _ipv4_valida(texto):
    for candidato in _IPV4.findall(texto):
        try:
            ip = ipaddress.IPv4Address(candidato)
        except ValueError:
            continue
        if not ip.is_unspecified:
            return str(ip)
    return None


def parsear_gateway_windows(salida):
    """Lee `route print -4 0.0.0.0` (independiente del idioma de Windows)."""
    mejor = None
    for linea in salida.splitlines():
        partes = linea.split()
        if len(partes) >= 5 and partes[0] == "0.0.0.0" and partes[1] == "0.0.0.0":
            gateway = _ipv4_valida(partes[2])
            if gateway is None:
                continue  # "On-link" u otro texto
            try:
                metrica = int(partes[4])
            except ValueError:
                metrica = 9999
            if mejor is None or metrica < mejor[0]:
                mejor = (metrica, gateway)
    return mejor[1] if mejor else None


def parsear_gateway_linux(salida):
    """Lee `ip route show default`: 'default via 192.168.1.1 dev wlan0 ...'."""
    for linea in salida.splitlines():
        if linea.startswith("default"):
            m = re.search(r"via\s+(\S+)", linea)
            if m:
                return _ipv4_valida(m.group(1))
    return None


def parsear_gateway_macos(salida):
    """Lee `route -n get default`: línea 'gateway: 192.168.1.1'."""
    for linea in salida.splitlines():
        if linea.strip().startswith("gateway:"):
            return _ipv4_valida(linea)
    return None


def parsear_proc_net_route(texto):
    """Lee /proc/net/route (Linux). Las IPs vienen en hexadecimal invertido."""
    for linea in texto.splitlines()[1:]:
        campos = linea.split()
        if len(campos) >= 3 and campos[1] == "00000000":
            try:
                octetos = bytes.fromhex(campos[2])[::-1]
            except ValueError:
                continue
            gateway = ".".join(str(b) for b in octetos)
            return _ipv4_valida(gateway)
    return None


def _ejecutar(comando):
    try:
        r = subprocess.run(
            comando, capture_output=True, text=True, errors="replace", timeout=10
        )
        return r.stdout
    except (OSError, subprocess.TimeoutExpired) as error:
        log.warning("No se pudo ejecutar %s: %s", comando[0], error)
        return ""


def obtener_gateway():
    """Puerta de enlace predeterminada, o None si no se puede determinar."""
    sistema = platform.system()
    if sistema == "Windows":
        return parsear_gateway_windows(_ejecutar(["route", "print", "-4", "0.0.0.0"]))
    if sistema == "Darwin":
        return parsear_gateway_macos(_ejecutar(["route", "-n", "get", "default"]))
    # Linux: primero /proc (no necesita comandos), luego `ip route`.
    try:
        with open("/proc/net/route", encoding="ascii") as f:
            gateway = parsear_proc_net_route(f.read())
        if gateway:
            return gateway
    except OSError:
        pass
    return parsear_gateway_linux(_ejecutar(["ip", "route", "show", "default"]))


def obtener_informacion_red():
    return {
        "equipo": obtener_nombre_equipo(),
        "ip_local": obtener_ip_local(),
        "gateway": obtener_gateway(),
    }
