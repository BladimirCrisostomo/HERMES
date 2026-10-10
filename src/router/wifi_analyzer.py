import re
import subprocess


class WiFiAnalyzer:
    """Analiza redes Wi-Fi visibles y recomienda un canal."""

    CANALES_RECOMENDADOS = (1, 6, 11)

    def escanear_redes(self):
        """Obtiene las redes visibles mediante Windows."""

        try:
            resultado = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                text=True,
                encoding="cp850",
                errors="replace",
                timeout=15
            )

            if resultado.returncode != 0:
                return {
                    "correcto": False,
                    "error": resultado.stderr.strip()
                    or "Windows no pudo realizar el escaneo."
                }

            texto = resultado.stdout

            canales = re.findall(
                r"(?:Canal|Channel)\s*:\s*(\d+)",
                texto,
                re.IGNORECASE
            )

            canales = [int(canal) for canal in canales]

            return {
                "correcto": True,
                "cantidad_redes": len(canales),
                "canales_detectados": canales
            }

        except (OSError, subprocess.TimeoutExpired) as error:
            return {
                "correcto": False,
                "error": str(error)
            }

    def analizar(self, datos):
        """Cuenta redes por canal y recomienda una opción."""

        if not datos.get("correcto"):
            return {
                "correcto": False,
                "error": datos.get("error", "Escaneo fallido.")
            }

        canales = datos["canales_detectados"]

        if not canales:
            return {
                "correcto": False,
                "error": (
                    "No se detectaron canales. Comprueba que "
                    "el Wi-Fi esté activado y vuelve a intentarlo."
                )
            }

        conteo = {
            canal: canales.count(canal)
            for canal in range(1, 14)
        }

        recomendacion = min(
            self.CANALES_RECOMENDADOS,
            key=lambda canal: conteo[canal]
        )

        return {
            "correcto": True,
            "cantidad_redes": len(canales),
            "redes_por_canal": conteo,
            "canal_recomendado": recomendacion,
            "criterio": "Menor número de redes detectadas"
        }