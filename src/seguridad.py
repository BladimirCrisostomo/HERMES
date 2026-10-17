"""Validaciones de entrada. Todo lo que viene del usuario o de la red pasa por aquí."""
import ipaddress
import logging
import re
import unicodedata

_HOST_VALIDO = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_MAC_VALIDA = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")


def sanitizar_texto(texto, longitud_maxima=300):
    """Quita caracteres de control y limita la longitud de una consulta."""
    if not isinstance(texto, str):
        return ""
    limpio = "".join(
        c for c in texto if c in " \t" or not unicodedata.category(c).startswith("C")
    )
    return limpio.strip()[:longitud_maxima]


def validar_host(host):
    """Acepta solo IPs o nombres de host. Evita que un valor como '-f' se
    interprete como opción del comando ping."""
    if not isinstance(host, str) or not _HOST_VALIDO.match(host):
        raise ValueError(f"Host no válido: {host!r}")
    return host


def es_ip_privada(ip):
    """True solo para direcciones de redes locales (192.168.x.x, 10.x.x.x, ...)."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def exigir_ip_privada(ip):
    """HERMES solo sondea equipos de la red local, nunca hosts de Internet."""
    if not es_ip_privada(ip):
        raise ValueError(
            f"{ip!r} no es una IP privada. HERMES solo analiza tu red local."
        )
    return ip


def validar_mac(mac):
    if not isinstance(mac, str) or not _MAC_VALIDA.match(mac):
        raise ValueError(f"MAC no válida: {mac!r}")
    return mac.upper().replace("-", ":")


# --- Protección de secretos en los logs --------------------------------------
_SECRETOS = set()


def registrar_secreto(valor):
    """Marca un texto (p. ej. una contraseña) para que nunca aparezca en los logs."""
    if isinstance(valor, str) and len(valor) >= 3:
        _SECRETOS.add(valor)


class FiltroSecretos(logging.Filter):
    """Reemplaza por *** cualquier secreto registrado que llegue a un mensaje de log."""

    def filter(self, record):
        mensaje = record.getMessage()
        for secreto in _SECRETOS:
            mensaje = mensaje.replace(secreto, "***")
        record.msg, record.args = mensaje, None
        return True
