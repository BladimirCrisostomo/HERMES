"""Descubrimiento de dispositivos de la red local (no requiere contraseña del router).

Cómo funciona: se envía un paquete UDP mínimo a cada IP de tu subred /24 para que
el sistema resuelva su MAC (ARP), y luego se lee la tabla ARP del sistema.
Solo se sondean IPs privadas de tu propia red.

Límites que conviene conocer:
 - Cuenta DISPOSITIVOS, no personas (una persona puede tener varios).
 - Un equipo apagado o en ahorro de energía profundo puede no aparecer.
 - Los móviles modernos usan MAC aleatoria/privada: pueden verse como "otro"
   dispositivo y bloquear por MAC puede no ser permanente. Se marcan con
   `mac_aleatoria=True`.
 - Se asume una subred /24 (la más común en redes domésticas).
"""
import csv
import ipaddress
import logging
import platform
import re
import socket
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from dataclasses import dataclass
from typing import Optional

from . import config, discovery
from .seguridad import exigir_ip_privada

log = logging.getLogger("hermes.dispositivos")

_IPV4 = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
_MAC = re.compile(r"(?<![0-9A-Fa-f:-])((?:[0-9A-Fa-f]{1,2}[:-]){5}[0-9A-Fa-f]{1,2})(?![0-9A-Fa-f:-])")

# Solo prefijos de los que estoy seguro. Para cubrir más fabricantes, descarga
# oui.csv del IEEE (standards-oui.ieee.org) y guárdalo como data/oui.csv.
OUI_CONOCIDOS = {
    "B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi",
    "005056": "VMware", "000C29": "VMware",
    "080027": "VirtualBox", "525400": "QEMU/KVM", "00155D": "Microsoft Hyper-V",
}
_oui_cache = {}


@dataclass
class Dispositivo:
    ip: str
    mac: Optional[str]
    fabricante: Optional[str] = None
    nombre: Optional[str] = None
    es_este_equipo: bool = False
    es_gateway: bool = False
    mac_aleatoria: bool = False


def normalizar_mac(mac):
    """'a-b-c-d-e-f' o 'A:B:C:D:E:F' -> 'AA:BB:CC:DD:EE:FF'."""
    return ":".join(p.zfill(2) for p in re.split(r"[:-]", mac)).upper()


def es_mac_aleatoria(mac):
    """Bit 'administrada localmente': lo activan iOS/Android/Windows al privatizar la MAC."""
    return bool(int(mac[:2], 16) & 0b10)


def cargar_oui():
    """OUI conocidos + data/oui.csv (formato IEEE o 'prefijo,fabricante') si existe."""
    if _oui_cache:
        return _oui_cache
    _oui_cache.update(OUI_CONOCIDOS)
    ruta = config.DATA_DIR / "oui.csv"
    if ruta.exists():
        try:
            with open(ruta, newline="", encoding="utf-8", errors="replace") as f:
                for fila in csv.reader(f):
                    if len(fila) >= 3 and re.fullmatch(r"[0-9A-Fa-f]{6}", fila[1].strip()):
                        _oui_cache[fila[1].strip().upper()] = fila[2].strip()      # formato IEEE
                    elif len(fila) >= 2 and re.fullmatch(r"[0-9A-Fa-f:-]{6,8}", fila[0].strip()):
                        _oui_cache[re.sub(r"[:-]", "", fila[0]).upper()[:6]] = fila[1].strip()
        except OSError as error:
            log.warning("No se pudo leer data/oui.csv: %s", error)
    return _oui_cache


def fabricante_de(mac):
    if not mac or es_mac_aleatoria(mac):
        return None
    return cargar_oui().get(mac.replace(":", "")[:6])


def parsear_tabla_arp(texto, red=None):
    """Convierte la salida de `arp -a`, `ip neigh` o /proc/net/arp en {ip: mac}.

    Descarta broadcast, multicast, entradas incompletas y IPs fuera de `red`.
    """
    tabla = {}
    for linea in texto.splitlines():
        ip_m, mac_m = _IPV4.search(linea), _MAC.search(linea)
        if not ip_m or not mac_m:
            continue
        try:
            ip = ipaddress.IPv4Address(ip_m.group(1))
        except ValueError:
            continue
        mac = normalizar_mac(mac_m.group(1))
        if mac in ("FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00") or mac.startswith(("01:00:5E", "33:33")):
            continue
        if ip.is_multicast:
            continue
        if red is not None and (ip not in red or ip in (red.network_address, red.broadcast_address)):
            continue
        tabla[str(ip)] = mac
    return tabla


def obtener_tabla_arp():
    sistema = platform.system()
    if sistema == "Windows":
        return discovery._ejecutar(["arp", "-a"])
    if sistema == "Darwin":
        return discovery._ejecutar(["arp", "-an"])
    try:
        with open("/proc/net/arp", encoding="ascii") as f:
            return f.read()
    except OSError:
        return discovery._ejecutar(["ip", "neigh", "show"])


def _poke(ip):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.2)
            s.sendto(b"\x00", (ip, 9))   # puerto 'discard': solo provoca la resolución ARP
    except OSError:
        pass


def sondear_subred(red, trabajadores=100):
    with ThreadPoolExecutor(max_workers=trabajadores) as pool:
        list(pool.map(_poke, (str(h) for h in red.hosts())))


def resolver_nombres(ips, timeout=2.0):
    """Nombres de host en paralelo, con tiempo máximo total."""
    def _nombre(ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except OSError:
            return None

    nombres = {}
    pool = ThreadPoolExecutor(max_workers=32)
    futuros = {pool.submit(_nombre, ip): ip for ip in ips}
    try:
        for f in as_completed(futuros, timeout=timeout):
            nombres[futuros[f]] = f.result()
    except TimeoutError:
        pass
    pool.shutdown(wait=False, cancel_futures=True)
    return nombres


def mac_propia():
    """MAC de este equipo (aproximada: la que Python considera principal)."""
    n = uuid.getnode()
    if (n >> 40) & 1:      # bit multicast = Python no pudo averiguarla
        return None
    return ":".join(f"{(n >> s) & 0xFF:02X}" for s in range(40, -8, -8))


def construir_dispositivos(tabla, ip_local, gateway, nombres=None, mac_local=None):
    """Arma la lista final (pura, sin red). Ordenada por IP."""
    tabla = dict(tabla)
    if ip_local and mac_local:
        tabla.setdefault(ip_local, mac_local)
    nombres = nombres or {}
    lista = [
        Dispositivo(
            ip=ip, mac=mac, fabricante=fabricante_de(mac), nombre=nombres.get(ip),
            es_este_equipo=(ip == ip_local), es_gateway=(ip == gateway),
            mac_aleatoria=es_mac_aleatoria(mac),
        )
        for ip, mac in tabla.items()
    ]
    if ip_local and ip_local not in tabla:
        lista.append(Dispositivo(ip=ip_local, mac=None, es_este_equipo=True))
    return sorted(lista, key=lambda d: ipaddress.IPv4Address(d.ip))


def escanear(ip_local=None, gateway=None, esperar=1.5, pasadas=2):
    """Escanea la subred local y devuelve la lista de Dispositivo."""
    ip_local = ip_local or discovery.obtener_ip_local()
    if not ip_local:
        raise RuntimeError("No se pudo determinar la IP local; ¿hay conexión a una red?")
    exigir_ip_privada(ip_local)
    red = ipaddress.ip_network(f"{ip_local}/24", strict=False)
    gateway = gateway or discovery.obtener_gateway()

    for _ in range(pasadas):   # una segunda pasada atrapa equipos lentos en despertar
        sondear_subred(red)
        time.sleep(esperar)
    tabla = parsear_tabla_arp(obtener_tabla_arp(), red)
    nombres = resolver_nombres(list(tabla))
    log.info("Escaneo de %s: %d dispositivos.", red, len(tabla))
    return construir_dispositivos(tabla, ip_local, gateway, nombres, mac_propia())


def macs_protegidas(dispositivos):
    """MAC que HERMES nunca debe bloquear ni limitar: este equipo y el router."""
    return {d.mac for d in dispositivos if d.mac and (d.es_este_equipo or d.es_gateway)}
