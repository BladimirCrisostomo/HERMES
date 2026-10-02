# Este archivo es un script de prueba para el detector de routers. Permite al usuario ingresar la IP del gateway y muestra los servicios detectados en el router.
from detector import RouterDetector


def main():

    gateway = "192.168.100.1"#este es el gateway que se va a analizar, es solo un ejemplo, se puede cambiar por cualquier otra IP de gateway

    detector = RouterDetector(gateway)

    resultado = detector.analizar()

    print("=== DETECTOR DE ROUTER ===")
    print(f"Gateway: {resultado['ip']}")

    print("\nServicios detectados:")

    for servicio, disponible in resultado["servicios"].items():

        estado = "DISPONIBLE" if disponible else "NO DISPONIBLE"

        print(f"{servicio.upper()}: {estado}")


if __name__ == "__main__":
    main()