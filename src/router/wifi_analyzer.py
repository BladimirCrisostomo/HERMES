"""Analiza las redes Wi-Fi visibles (2.4 GHz) y recomienda un canal.

Soporta Windows (netsh) y Linux (nmcli). Solo se extraen los canales; no se
guardan nombres de redes de terceros.
"""
import platform
import re
import subprocess

CANALES_RECOMENDADOS = (1, 6, 11)   # los únicos que no se solapan entre sí
_CANAL_WINDOWS = re.compile(r"(?:Canal|Channel)\s*:\s*(\d+)", re.IGNORECASE)


def parsear_canales_windows(texto):
    return [int(c) for c in _CANAL_WINDOWS.findall(texto)]


def parsear_canales_nmcli(texto):
    """`nmcli -t -f CHAN dev wifi list` -> una línea por red con el canal."""
    return [int(l.strip()) for l in texto.splitlines() if l.strip().isdigit()]


def interferencia(canales, candidato):
    """Puntaje de interferencia en `candidato`.

    Una red en el canal c afecta a los canales a ≤4 de distancia (en 2.4 GHz los
    canales se solapan): peso 1 en el mismo canal, decreciendo hasta 0.
    """
    return sum(max(0.0, 1 - abs(c - candidato) / 5) for c in canales if 1 <= c <= 14)


class WiFiAnalyzer:
    CANALES_RECOMENDADOS = CANALES_RECOMENDADOS

    def escanear_redes(self):
        sistema = platform.system()
        if sistema == "Windows":
            comando, parser = ["netsh", "wlan", "show", "networks", "mode=bssid"], parsear_canales_windows
        elif sistema == "Linux":
            comando, parser = ["nmcli", "-t", "-f", "CHAN", "dev", "wifi", "list"], parsear_canales_nmcli
        else:
            return {"correcto": False, "error": f"Escaneo Wi-Fi no soportado en {sistema}."}
        try:
            r = subprocess.run(comando, capture_output=True, text=True,
                               errors="replace", timeout=15)
        except (OSError, subprocess.TimeoutExpired) as error:
            return {"correcto": False, "error": str(error)}
        if r.returncode != 0:
            return {"correcto": False,
                    "error": r.stderr.strip() or "El sistema no pudo realizar el escaneo."}
        canales = parser(r.stdout)
        return {"correcto": True, "cantidad_redes": len(canales), "canales_detectados": canales}

    def analizar(self, datos):
        if not datos.get("correcto"):
            return {"correcto": False, "error": datos.get("error", "Escaneo fallido.")}
        canales = datos["canales_detectados"]
        if not canales:
            return {"correcto": False, "error": (
                "No se detectaron canales. Comprueba que el Wi-Fi esté activado "
                "(en Windows 11 también el permiso de ubicación) y vuelve a intentarlo.")}

        canales_24 = [c for c in canales if c <= 14]
        puntajes = {c: round(interferencia(canales_24, c), 2) for c in CANALES_RECOMENDADOS}
        mejor = min(CANALES_RECOMENDADOS, key=lambda c: (puntajes[c], c))
        return {
            "correcto": True,
            "cantidad_redes": len(canales),
            "redes_5ghz_ignoradas": len(canales) - len(canales_24),
            "redes_por_canal": {c: canales_24.count(c) for c in range(1, 14)},
            "interferencia_por_canal": puntajes,
            "canal_recomendado": mejor,
            "criterio": "Menor interferencia considerando solapamiento de canales vecinos",
        }
