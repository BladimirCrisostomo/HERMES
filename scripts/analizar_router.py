"""Exploración manual y de solo lectura del router (reemplaza los antiguos test_*.py).

Uso:  python -m scripts.analizar_router [IP_DEL_ROUTER]
Sin argumento usa el gateway detectado automáticamente.
"""
import sys

from src import discovery
from src.router.capability_detector import RouterCapabilityDetector
from src.router.router_profile import RouterProfile


def main():
    red = discovery.obtener_informacion_red()
    gateway = sys.argv[1] if len(sys.argv) > 1 else red["gateway"]
    if not gateway:
        print("No se pudo detectar el gateway. Pásalo como argumento.")
        return

    print("=== RED LOCAL ===")
    for k, v in red.items():
        print(f"{k}: {v}")

    resultado = RouterCapabilityDetector(gateway).detectar()
    perfil = RouterProfile()
    perfil.actualizar({"ip_gateway": gateway, **resultado["informacion"],
                       **{f"cap_{k}": v for k, v in resultado["capacidades"].items()}})
    print()
    perfil.mostrar()
    print("\nEvidencias:", resultado["evidencias"])
    print("\nHERMES no ha modificado la configuración del router.")


if __name__ == "__main__":
    main()
