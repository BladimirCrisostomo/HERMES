# Este archivo contiene funciones para obtener información de red del sistema.
import socket


def obtener_nombre_equipo():
    """
    Obtiene el nombre del equipo donde se está ejecutando HERMES.
    """
    return socket.gethostname()


def obtener_ip_local():
    """
    Obtiene la dirección IP local del equipo.
    """
    try:
        conexion = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # No se establece una conexión real.
        # Se utiliza para determinar qué interfaz de red
        # utilizaría el sistema para comunicarse.
        conexion.connect(("8.8.8.8", 80))

        ip = conexion.getsockname()[0]

        conexion.close()

        return ip

    except Exception:
        return None


def obtener_gateway():
    """
    Obtiene la puerta de enlace predeterminada del sistema.
    """

    try:
        import subprocess

        resultado = subprocess.run(#hace un comando en la terminal para obtener la información de red
            ["ipconfig"],
            capture_output=True,
            text=True,
            encoding="cp850"
        )

        lineas = resultado.stdout.splitlines()

        for linea in lineas:
            if "Puerta de enlace predeterminada" in linea:
                gateway = linea.split(":")[-1].strip()

                if gateway:
                    return gateway

    except Exception:
        pass

    return None


def obtener_informacion_red():
    """
    Reúne información básica de la red.
    """

    return {
        "equipo": obtener_nombre_equipo(),
        "ip_local": obtener_ip_local(),
        "gateway": obtener_gateway()
    }