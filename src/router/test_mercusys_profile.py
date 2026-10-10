import sys
from pathlib import Path

# Permite importar los módulos desde la carpeta principal HERMES.
CARPETA_PROYECTO = Path(__file__).resolve().parents[2]

if str(CARPETA_PROYECTO) not in sys.path:
    sys.path.insert(0, str(CARPETA_PROYECTO))

from src.discovery import obtener_informacion_red
from src.router.detector import RouterDetector
from src.router.web_info import RouterWebInfo
from src.router.device_profile import obtener_perfil_mw306r


def main():
    print("=== HERMES: PERFIL MERCUSYS MW306R ===\n")

    # 1. Cargar los datos conocidos del equipo.
    perfil = obtener_perfil_mw306r()

    print("=== IDENTIFICACIÓN DEL EQUIPO ===")
    print(f"Fabricante: {perfil['fabricante']}")
    print(f"Modelo: {perfil['modelo']}")
    print(f"Hardware: {perfil['hardware']}")
    print(f"Firmware: {perfil['firmware']}")
    print(f"Región: {perfil['region'] or 'Pendiente de identificar'}")
    print(f"Fuente: {perfil['fuente_identificacion']}")

    # 2. Descubrir la red actual.
    red = obtener_informacion_red()
    gateway = red.get("gateway")

    print("\n=== RED LOCAL ===")
    print(f"Equipo: {red.get('equipo')}")
    print(f"IP local: {red.get('ip_local')}")
    print(f"Gateway: {gateway}")

    if not gateway:
        print("\nNo se pudo identificar el gateway.")
        return

    # 3. Detectar servicios de forma no intrusiva.
    detector = RouterDetector(gateway)
    servicios = detector.detectar_servicios()

    print("\n=== SERVICIOS DETECTADOS ===")
    for servicio, disponible in servicios.items():
        estado = "Detectado" if disponible else "No detectado"
        print(f"{servicio.upper()}: {estado}")

    # 4. Consultar la página web sin iniciar sesión.
    analizador = RouterWebInfo(gateway)
    resultado = analizador.consultar("http")

    print("\n=== INTERFAZ WEB ===")

    if "error" in resultado:
        print("Consulta HTTP fallida.")
        print(f"Motivo: {resultado['error']}")
    else:
        print("Consulta HTTP correcta.")
        print(f"Código HTTP: {resultado.get('codigo')}")
        print(f"Servidor: {resultado.get('servidor')}")
        print(
            "Fabricante mencionado en la página: "
            f"{resultado.get('fabricante_detectado')}"
        )

    # 5. Mostrar las capacidades que falta verificar.
    print("\n=== CAPACIDADES PENDIENTES ===")

    for nombre, disponible in perfil["capacidades"].items():
        if disponible is None:
            estado = "PENDIENTE DE VERIFICACIÓN"
        else:
            estado = "VERIFICADA" if disponible else "NO DISPONIBLE"

        print(f"{nombre}: {estado}")

    print("\nPrueba terminada. No se modificó la configuración.")


if __name__ == "__main__":
    main()