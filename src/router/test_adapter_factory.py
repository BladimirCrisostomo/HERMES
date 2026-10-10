
from adapter_factory import RouterAdapterFactory
from manager import RouterManager


def main():
    gateway = "192.168.100.1"

    print("=== SELECCIÓN AUTOMÁTICA DE ADAPTADOR ===")

    fabrica = RouterAdapterFactory(gateway)
    resultado = fabrica.crear_adaptador()

    print(f"Tipo seleccionado: {resultado['tipo']}")
    print(f"Servicios: {resultado['servicios']}")
    print(f"Motivo: {resultado['motivo']}")

    adaptador = resultado["adaptador"]

    if adaptador is None:
        print("No se pudo crear un adaptador compatible.")
        return

    administrador = RouterManager()
    administrador.establecer_router(adaptador)

    print("\n=== CONSULTA MEDIANTE ROUTER MANAGER ===")

    respuesta = administrador.consultar_interfaz("/")

    for nombre, valor in respuesta.items():
        print(f"{nombre}: {valor}")


if __name__ == "__main__":
    main()
