"""Analiza la portada web del router (sin iniciar sesión)."""
import re

from . import http_client

FABRICANTES = [
    "Realtek Semiconductor Corp.", "TP-Link", "MERCUSYS", "NETGEAR", "D-Link",
    "Huawei", "ZTE", "MikroTik", "ASUS", "Tenda",
]
_TITULO = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_LOGIN = re.compile(r"""["']([^"']*login[^"']*)["']""", re.IGNORECASE)


def obtener_titulo(html):
    m = _TITULO.search(html)
    return m.group(1).strip() if m else None


def obtener_ruta_login(html):
    m = _LOGIN.search(html)
    return m.group(1) if m else None


def detectar_fabricante(html):
    minusculas = html.lower()
    return next((f for f in FABRICANTES if f.lower() in minusculas), None)


class RouterWebInfo:
    def __init__(self, ip):
        self.ip = ip

    def consultar(self, protocolo="http"):
        """Datos de la portada. No devuelve el HTML completo, solo metadatos."""
        r = http_client.obtener(self.ip, "/", protocolo)
        if not r["correcto"]:
            return {"url": r["url"], "error": r["error"]}
        html = r["cuerpo"]
        return {
            "url": r["url"], "codigo": r["codigo"], "servidor": r["servidor"],
            "tipo_contenido": r["tipo_contenido"], "titulo": obtener_titulo(html),
            "tamano": len(html),
            "formularios": len(re.findall(r"<form\b", html, re.IGNORECASE)),
            "fabricante_detectado": detectar_fabricante(html),
            "ruta_login": obtener_ruta_login(html),
        }
