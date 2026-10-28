"""Cliente HTTP mínimo y de solo lectura para hablar con el router.

Centraliza lo que antes estaba duplicado en web_info.py y generic_http.py:
solo GET, tiempo límite, tamaño máximo de respuesta y solo IPs privadas.
"""
import ssl
import urllib.request
from urllib.error import HTTPError, URLError

from ..seguridad import exigir_ip_privada

USER_AGENT = "HERMES-Network-Manager/1.0"
MAX_BYTES = 200_000   # no se descarga más que esto de la página del router


def obtener(ip, ruta="/", protocolo="http", timeout=3):
    """GET a http(s)://<ip><ruta>. Nunca lanza excepciones de red: devuelve un dict."""
    exigir_ip_privada(ip)
    if protocolo not in ("http", "https"):
        raise ValueError("El protocolo debe ser 'http' o 'https'.")
    if not ruta.startswith("/"):
        raise ValueError("La ruta debe comenzar con '/'.")

    url = f"{protocolo}://{ip}{ruta}"
    solicitud = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")

    # Los routers usan certificados autofirmados; solo lectura de la portada,
    # por eso aquí no se exige validar el certificado.
    contexto = None
    if protocolo == "https":
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(solicitud, timeout=timeout, context=contexto) as r:
            cuerpo = r.read(MAX_BYTES)
            return {
                "correcto": True, "url": r.geturl(), "codigo": r.status,
                "servidor": r.headers.get("Server"),
                "tipo_contenido": r.headers.get("Content-Type"),
                "cuerpo": cuerpo.decode("utf-8", errors="ignore"),
            }
    except HTTPError as error:
        return {"correcto": False, "url": url, "codigo": error.code, "error": str(error)}
    except (URLError, TimeoutError, OSError) as error:
        return {"correcto": False, "url": url, "error": str(error)}


def enviar_texto_estado(ip, ruta, cuerpo, protocolo="http", timeout=5):
    """POST de texto plano. Devuelve (código_http, cuerpo) y NO lanza error por un 401/404.

    Los paneles tipo 'code=...&asyn=...' entregan datos útiles incluso en respuestas 401
    (así obtienen los parámetros de login). Solo lanza OSError si falla la red.
    """
    exigir_ip_privada(ip)
    if protocolo not in ("http", "https") or not ruta.startswith("/"):
        raise ValueError("Protocolo o ruta no válidos.")
    solicitud = urllib.request.Request(
        f"{protocolo}://{ip}{ruta}", data=cuerpo.encode("utf-8"), method="POST",
        headers={"User-Agent": USER_AGENT, "Content-Type": "text/plain;charset=UTF-8",
                 "X-Requested-With": "XMLHttpRequest"})
    try:
        with urllib.request.urlopen(solicitud, timeout=timeout) as r:
            return r.status, r.read(MAX_BYTES * 5).decode("utf-8", errors="ignore")
    except HTTPError as error:
        return error.code, error.read(MAX_BYTES).decode("utf-8", errors="ignore")
