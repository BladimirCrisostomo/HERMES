"""Registro de adaptadores: identifica el router y elige el adaptador adecuado.

Cada adaptador se registra con una función `puntuar(huella)` que devuelve un número
(0 = no es mío; más alto = más seguro de que es mío). Gana el de mayor puntaje.
La 'huella' del router sale de su portada web y de sus puertos abiertos.

Todavía no hay adaptadores para routers reales: se agregan copiando
adapters/plantilla.py y registrándolos aquí con `registrar_adaptador`.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable

from ..credenciales import advertencia_transporte
from ..seguridad import es_ip_privada, exigir_ip_privada
from .adapters.mercusys_mw306r import ErrorRouter, MercusysMW306R, responde_al_protocolo
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
        "protocolo_panel": responde_al_protocolo(ip) if servicios.get("http") else False,
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
            "HERMES no tiene un adaptador para este equipo: puede diagnosticar la red y listar "
            "dispositivos, pero no administrarlo (para añadir uno, ver "
            "src/router/adapters/plantilla.py).")}
    if credenciales is None:
        return {"correcto": False, "huella": huella, "adaptador": info.nombre,
                "error": "Se necesitan usuario y contraseña del router."}

    advertencias = []
    aviso = advertencia_transporte(huella["servicios"])
    if aviso:
        advertencias.append(aviso)
    router = info.crear(ip, credenciales)
    try:
        router.conectar()
    except NotImplementedError as error:      # adaptador todavía incompleto
        return {"correcto": False, "huella": huella, "adaptador": info.nombre, "error": str(error),
                "router": router}
    except ErrorRouter as error:               # contraseña rechazada, modelo distinto, etc.
        return {"correcto": False, "huella": huella, "adaptador": info.nombre, "error": str(error),
                "router": router}
    except OSError as error:
        return {"correcto": False, "huella": huella, "adaptador": info.nombre, "router": router,
                "error": f"No se pudo conectar con el router: {error}"}
    return {"correcto": True, "router": router, "adaptador": info.nombre,
            "advertencias": advertencias}


def _puntuar_mercusys(huella):
    """Habla el protocolo del panel (70) o al menos dice ser Mercusys (50).

    El adaptador está validado solo con el MW306R V1: al conectar, comprueba el modelo
    y se niega a operar con cualquier otro.
    """
    if huella.get("protocolo_panel"):
        return 70
    texto = " ".join(str(huella.get(k) or "") for k in ("fabricante", "titulo", "servidor")).upper()
    return 50 if "MERCUSYS" in texto else 0


registrar_adaptador(InfoAdaptador(
    "mercusys_mw306r", _puntuar_mercusys, lambda ip, cred: MercusysMW306R(ip, cred)))


CANDIDATOS_COMUNES = ("192.168.1.1", "192.168.0.1", "192.168.100.1", "192.168.2.1", "10.0.0.1", "192.168.8.1")


def buscar_routers(extra=()):
    """Sondea las IPs de router más comunes (y las de `extra`) y dice cuáles son compatibles.

    Devuelve [{ip, adaptador (nombre | None), servidor, titulo}] solo de los que tienen web.
    """
    ips = [ip for ip in dict.fromkeys([*extra, *CANDIDATOS_COMUNES]) if es_ip_privada(ip)]

    def sondear(ip):
        try:
            if not RouterDetector(ip).comprobar_puerto(80, timeout=0.8):
                return None
            huella = obtener_huella(ip)
            info, _ = elegir_adaptador(huella)
            return {"ip": ip, "adaptador": info.nombre if info else None,
                    "servidor": huella.get("servidor"), "titulo": huella.get("titulo")}
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=max(1, len(ips))) as pool:
        return [r for r in pool.map(sondear, ips) if r]
