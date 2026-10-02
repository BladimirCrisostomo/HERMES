# Este archivo contiene la clase RouterDetector, que se encarga de detectar servicios en un router dado su IP.
import socket


class RouterDetector:#esta clase se encarga de detectar servicios en un router dado su IP

    def __init__(self, ip):
        self.ip = ip

    def comprobar_puerto(self, puerto, timeout=1):
        """
        Comprueba si un puerto TCP del gateway está disponible.
        """

        try:
            conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conexion.settimeout(timeout)

            resultado = conexion.connect_ex((self.ip, puerto))

            conexion.close()

            return resultado == 0

        except Exception:
            return False

    def detectar_servicios(self):
        """
        Detecta algunos servicios de administración comunes.
        """

        servicios = {
            "http": self.comprobar_puerto(80),
            "https": self.comprobar_puerto(443),
            "ssh": self.comprobar_puerto(22),
        }

        return servicios

    def analizar(self):
        """
        Realiza un análisis básico del gateway.
        """

        servicios = self.detectar_servicios()

        return {
            "ip": self.ip,
            "servicios": servicios
        }