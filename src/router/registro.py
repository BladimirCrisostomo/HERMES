"""Registro de adaptadores: identifica el router y elige el adaptador adecuado.

Cada adaptador se registra con una función `puntuar(huella)` que devuelve un número
(0 = no es mío; más alto = más seguro de que es mío). Gana el de mayor puntaje.
La 'huella' del router sale de su portada web y de sus puertos abiertos.

Todavía no hay adaptadores para routers reales: se agregan copiando
adapters/plantilla.py y registrándolos aquí con `registrar_adaptador`.
"""
from dataclasses import dataclass
from typing import Callable

from ..credenciales import advertencia_transporte
from ..seguridad import exigir_ip_privada
from .adapters.simulado import RouterSimulado
from .detector import RouterDetector
from .web_info import RouterWebInfo


@dataclass
class InfoAdaptador:
    nombre: str
    puntuar: Callable   # (huella: dict) -> int
    crear: Callable     # (ip, credenciales) -> RouterController


_ADAPTADORES = []


def registrar_adaptador(info):
    _ADAPTADORES.append(info)


def adaptadores_registrados():
    return [a.nombre for a in _ADAPTADORES]


def obtener_huella(ip):
    """Datos observables del router sin iniciar sesión."""
    exigir_ip_privada(ip)
    servicios = RouterDetector(ip).detectar_servicios()
    web = RouterWebInfo(ip).consultar("http") if servicios.get("http") else {}
    return {
        "ip": ip, "servicios": servicios,
        "servidor": web.get("servidor"), "titulo": web.get("titulo"),
        "fabricante": web.get("fabricante_detectado"), "ruta_login": web.get("ruta_login"),
    }


def elegir_adaptador(huella):
    """(InfoAdaptador, puntaje) del mejor candidato, o (None, 0)."""
    mejor, mejor_puntaje = None, 0
    for info in _ADAPTADORES:
        puntaje = info.puntuar(huella)
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = info, puntaje
    return mejor, mejor_puntaje


def conectar_router(ip, credenciales=None, simulacion=False):
    """Devuelve un dict: correcto, router, adaptador, advertencias, error."""
    if simulacion:
        router = RouterSimulado()
        router.conectar()
        return {"correcto": True, "router": router, "adaptador": "simulado",
                "advertencias": ["MODO SIMULACIÓN: no se modifica ningún router real."]}

    huella = obtener_huella(ip)
    info, puntaje = elegir_adaptador(huella)
    if info is None:
        return {"correcto": False, "huella": huella, "error": (
            "No hay un adaptador para este router. HERMES puede diagnosticar la red y "
            "listar dispositivos, pero para administrarlo hace falta crear uno "
            "(ver src/router/adapters/plantilla.py).")}
    if credenciales is None:
        return {"correcto": False, "huella": huella, "adaptador": info.nombre,
                "error": "Se necesitan usuario y contraseña del router."}

    advertencias = []
    aviso = advertencia_transporte(huella["servicios"])
    if aviso:
        advertencias.append(aviso)
    router = info.crear(ip, credenciales)
    router.conectar()
    return {"correcto": True, "router": router, "adaptador": info.nombre,
            "advertencias": advertencias}
