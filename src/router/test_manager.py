
from adapters.generic_http import GenericHTTPAdapter
from manager import RouterManager


def main():
    gateway = "192.168.100.1"

    # Crear el adaptador HTTP.
    adaptador = GenericHTTPAdapter(gateway)

    # Registrar el adaptador en el administrador.
    administrador = RouterManager()
    administrador.establecer_router(adaptador)

    print("=== PRUEBA DE ROUTER MANAGER ===")
    print(f"Adaptador registrado: {administrador.conectado()}")

    # Consultar la interfaz del router.
    resultado = administrador.consultar_interfaz("/")

    for nombre, valor in resultado.items():
        print(f"{nombre}: {valor}")


if __name__ == "__main__":
    main()
