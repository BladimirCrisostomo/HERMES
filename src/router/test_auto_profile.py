import sys
from pathlib import Path

# Obtener la carpeta raíz del proyecto HERMES.
CARPETA_PROYECTO = Path(__file__).resolve().parents[2]

# Agregar la raíz del proyecto a las rutas de búsqueda.
sys.path.insert(0, str(CARPETA_PROYECTO))

from src.discovery import obtener_informacion_red
from detector import RouterDetector
from src.router.web_info import RouterWebInfo
from src.router.router_profile import RouterProfile
from adapter_factory import RouterAdapterFactory
from manager import RouterManager


def main():
    print("=== HERMES: PERFIL AUTOMÁTICO DEL ROUTER ===\n")

    # 1. Descubrir la información de nuestra red.
    red = obtener_informacion_red()
    gateway = red.get("gateway")

    if not gateway:
        print("No se pudo detectar el gateway.")
        print("Comprueba la conexión de red e inténtalo de nuevo.")
        return

    print(f"Gateway detectado: {gateway}")

    # 2. Crear el perfil que almacenará los resultados.
    perfil = RouterProfile()

    perfil.actualizar({
        "equipo_local": red.get("equipo"),
        "ip_local": red.get("ip_local"),
        "ip_gateway": gateway,
    })

    # 3. Detectar los servicios de red disponibles.
    detector = RouterDetector(gateway)
    servicios = detector.detectar_servicios()

    perfil.establecer("servicios_detectados", servicios)

    # 4. Consultar la interfaz web sin iniciar sesión.
    analizador_web = RouterWebInfo(gateway)
    informacion_web = analizador_web.consultar("http")

    if "error" not in informacion_web:
        perfil.actualizar({
            "http_consulta_correcta": True,
            "servidor_web": informacion_web.get("servidor"),
            "codigo_http": informacion_web.get("codigo"),
            "fabricante_detectado": (
                informacion_web.get("fabricante_detectado")
            ),
            "ruta_login_detectada": (
                informacion_web.get("ruta_login")
            ),
        })
    else:
        perfil.actualizar({
            "http_consulta_correcta": False,
            "error_http": informacion_web["error"],
        })

    # 5. Seleccionar automáticamente un adaptador compatible.
    fabrica = RouterAdapterFactory(gateway)
    seleccion = fabrica.crear_adaptador()

    adaptador = seleccion.get("adaptador")

    perfil.actualizar({
        "tipo_adaptador": seleccion.get("tipo"),
        "motivo_seleccion": seleccion.get("motivo"),
    })

    # 6. Registrar el adaptador y realizar una consulta de prueba.
    administrador = RouterManager()

    if adaptador is not None:
        administrador.establecer_router(adaptador)

        respuesta = administrador.consultar_interfaz("/")

        perfil.establecer(
            "adaptador_registrado",
            administrador.conectado()
        )
        perfil.establecer(
            "consulta_adaptador_correcta",
            respuesta.get("correcto", False)
        )
        perfil.establecer(
            "respuesta_adaptador",
            respuesta
        )
    else:
        perfil.establecer("adaptador_registrado", False)
        perfil.establecer("consulta_adaptador_correcta", False)

    # 7. Mostrar el informe final.
    print("\n")
    perfil.mostrar()

    print("\n=== RESUMEN ===")
    print(f"Gateway: {gateway}")
    print(f"Adaptador: {seleccion.get('tipo')}")
    print(f"HTTP disponible: {servicios.get('http')}")
    print(f"HTTPS disponible: {servicios.get('https')}")
    print(f"SSH disponible: {servicios.get('ssh')}")

    print("\nNota: detectar un servicio no garantiza")
    print("que HERMES tenga permisos para administrar el router.")


if __name__ == "__main__":
    main()