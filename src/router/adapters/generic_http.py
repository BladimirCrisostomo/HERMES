
import urllib.request
from urllib.error import HTTPError, URLError


class GenericHTTPAdapter:
    """
    Adaptador genérico de solo lectura para interfaces HTTP.

    No inicia sesión ni modifica la configuración del router.
    """

    def __init__(self, ip, timeout=3):
        self.ip = ip
        self.timeout = timeout

    def consultar(self, ruta="/"):
        """
        Consulta una ruta HTTP del router y devuelve metadatos.
        """

        if not ruta.startswith("/"):
            raise ValueError(
                "La ruta debe comenzar con '/'."
            )

        url = f"http://{self.ip}{ruta}"

        solicitud = urllib.request.Request(
            url,
            headers={
                "User-Agent": "HERMES-Network-Manager/1.0"
            },
            method="GET"
        )

        try:
            with urllib.request.urlopen(
                solicitud,
                timeout=self.timeout
            ) as respuesta:

                return {
                    "correcto": True,
                    "url": respuesta.geturl(),
                    "codigo": respuesta.status,
                    "servidor": respuesta.headers.get("Server"),
                    "tipo_contenido": respuesta.headers.get(
                        "Content-Type"
                    ),
                }

        except HTTPError as error:
            return {
                "correcto": False,
                "url": url,
                "codigo": error.code,
                "error": str(error),
            }

        except (URLError, TimeoutError, OSError) as error:
            return {
                "correcto": False,
                "url": url,
                "error": str(error),
            }
