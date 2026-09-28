#codigo para obtener los datos de la red y diagnosticar problemas de conectividad, latencia y perdida de paquetes

import socket#libreria para obtener el nombre del host y la dirección IP local
import subprocess#libreria para ejecutar comandos del sistema
import re#libreria para buscar patrones en cadenas de texto


def obtener_datos_red():#inicio de la funcion obtener_datos_red

    hostname = socket.gethostname()

    try:#intentar obtener la dirección IP local
        ip_local = socket.gethostbyname(hostname)
    except socket.error:
        ip_local = "No disponible"

    resultado = subprocess.run(
        ["ping", "8.8.8.8", "-n", "10"],
        capture_output=True,
        text=True
    )

    conexion = resultado.returncode == 0

    latencia = None
    perdida = None

    paquetes = re.search(
        r"Paquetes: enviados = (\d+), recibidos = (\d+), perdidos = (\d+)",
        resultado.stdout
    )

    if paquetes:

        enviados = int(paquetes.group(1))
        recibidos = int(paquetes.group(2))
        perdidos = int(paquetes.group(3))

        if enviados > 0:
            perdida = (perdidos / enviados) * 100

    latencia_resultado = re.search(
        r"Media = (\d+)ms",
        resultado.stdout
    )

    if latencia_resultado:
        latencia = int(latencia_resultado.group(1))

    return hostname, ip_local, conexion, latencia, perdida#para devolver los valores obtenidos de la red