
from adapters.generic_http import GenericHTTPAdapter


def main():
    gateway = "192.168.100.1"

    adaptador = GenericHTTPAdapter(gateway)

    print("=== PRUEBA DEL ADAPTADOR HTTP ===")

    resultado = adaptador.consultar("/")

    for nombre, valor in resultado.items():
        print(f"{nombre}: {valor}")


if __name__ == "__main__":
    main()
