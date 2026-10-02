#este archivo se encarga de consultar la página principal del router sin autenticarse, para obtener información sobre el servidor y el tipo de contenido que devuelve.
import urllib.request
import re


class RouterWebInfo:

    def __init__(self, ip):
        self.ip = ip

    def consultar(self, protocolo="http"):
        """
        Consulta la página principal del router sin autenticarse
        y obtiene información básica de la interfaz web.
        """

        url = f"{protocolo}://{self.ip}/"

        try:
            solicitud = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "HERMES-Network-Manager/1.0"
                }
            )

            with urllib.request.urlopen(
                solicitud,
                timeout=3
            ) as respuesta:

                contenido = respuesta.read()

                texto = contenido.decode(
                    "utf-8",
                    errors="ignore"
                )

                titulo = self.obtener_titulo(texto)

                formularios = len(
                    re.findall(
                        r"<form\b",
                        texto,
                        re.IGNORECASE
                    )
                )

                return {
                    "url": url,
                    "codigo": respuesta.status,
                    "servidor": respuesta.headers.get("Server"),
                    "tipo_contenido": respuesta.headers.get(
                        "Content-Type"
                    ),
                    "titulo": titulo,
                    "tamano": len(contenido),
                    "formularios": formularios,
                    "fabricante_detectado": self.detectar_fabricante(
                        texto
                    ),
                    "ruta_login": self.obtener_ruta_login(
                        texto
                    ),
                    "contenido": texto
                }

        except Exception as error:

            return {
                "url": url,
                "error": str(error)
            }

    def obtener_titulo(self, html):
        """
        Extrae el contenido de la etiqueta <title>.
        """

        coincidencia = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            re.IGNORECASE | re.DOTALL
        )

        if coincidencia:
            return coincidencia.group(1).strip()

        return None

    def obtener_ruta_login(self, html):
        """
        Busca una ruta de inicio de sesión dentro del HTML.
        """

        patrones = [
            r'["\']([^"\']*login[^"\']*)["\']',
            r'["\']([^"\']*Login[^"\']*)["\']'
        ]

        for patron in patrones:

            coincidencia = re.search(
                patron,
                html,
                re.IGNORECASE
            )

            if coincidencia:
                return coincidencia.group(1)

        return None

    def detectar_fabricante(self, html):
        """
        Busca fabricantes conocidos dentro del HTML.
        """

        fabricantes = [
            "Realtek Semiconductor Corp.",
            "TP-Link",
            "NETGEAR",
            "D-Link",
            "Huawei",
            "ZTE",
            "MikroTik",
            "ASUS",
            "Tenda"
        ]

        html_minusculas = html.lower()

        for fabricante in fabricantes:

            if fabricante.lower() in html_minusculas:
                return fabricante

        return None