"""Manejo seguro de las credenciales del router.

Reglas:
 - La contraseña nunca se escribe en el código, el repositorio ni los logs.
 - Se pide con getpass (no se ve al teclear) y vive solo en memoria.
 - Guardarla en el llavero del sistema (Windows Credential Manager, etc.) es
   opcional y solo ocurre si el usuario lo decide.
"""
import getpass
import logging
import os
from dataclasses import dataclass, field

from .seguridad import exigir_ip_privada, registrar_secreto

log = logging.getLogger("hermes.credenciales")
_SERVICIO = "HERMES-router"


@dataclass
class Credenciales:
    usuario: str
    contrasena: str = field(repr=False)   # repr=False: no aparece al imprimir el objeto

    def __post_init__(self):
        registrar_secreto(self.contrasena)

    def __str__(self):
        return f"Credenciales(usuario={self.usuario!r}, contrasena=***)"


def pedir_credenciales(ip, usuario_defecto="admin", entrada=input, clave=getpass.getpass):
    """Pregunta usuario y contraseña por consola (la contraseña no se muestra)."""
    exigir_ip_privada(ip)
    usuario = entrada(f"Usuario del router {ip} [{usuario_defecto}]: ").strip() or usuario_defecto
    contrasena = clave("Contraseña (no se mostrará): ")
    if not contrasena:
        raise ValueError("La contraseña no puede estar vacía.")
    return Credenciales(usuario, contrasena)


def desde_entorno():
    """Lee HERMES_ROUTER_USER / HERMES_ROUTER_PASS si existen (útil para pruebas)."""
    usuario = os.environ.get("HERMES_ROUTER_USER")
    contrasena = os.environ.get("HERMES_ROUTER_PASS")
    if usuario and contrasena:
        return Credenciales(usuario, contrasena)
    return None


def _llavero():
    try:
        import keyring
        return keyring
    except ImportError:
        return None


def guardar_en_llavero(ip, credenciales):
    """Guarda las credenciales en el llavero del sistema. False si no está disponible."""
    k = _llavero()
    if k is None:
        return False
    k.set_password(_SERVICIO, f"{ip}|{credenciales.usuario}", credenciales.contrasena)
    k.set_password(_SERVICIO, f"{ip}|usuario", credenciales.usuario)
    log.info("Credenciales de %s guardadas en el llavero del sistema.", ip)
    return True


def cargar_de_llavero(ip):
    k = _llavero()
    if k is None:
        return None
    usuario = k.get_password(_SERVICIO, f"{ip}|usuario")
    contrasena = k.get_password(_SERVICIO, f"{ip}|{usuario}") if usuario else None
    return Credenciales(usuario, contrasena) if usuario and contrasena else None


def advertencia_transporte(servicios):
    """Texto de aviso si el router solo ofrece HTTP (la contraseña viaja sin cifrar)."""
    if servicios.get("https"):
        return None
    return ("Este router solo ofrece HTTP: tu usuario y contraseña viajarán sin cifrar "
            "por tu red local. Úsalo solo en una red propia y de confianza.")
