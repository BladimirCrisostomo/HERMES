from capabilities import RouterCapabilities


def main():

    capacidades = RouterCapabilities()

    capacidades.establecer("http", True)
    capacidades.establecer("https", True)
    capacidades.establecer("ssh", False)

    capacidades.establecer("wifi", True)
    capacidades.establecer("cambiar_canal", True)
    capacidades.establecer("clientes", True)
    capacidades.establecer("bloqueo", True)
    capacidades.establecer("qos", False)

    capacidades.mostrar()


if __name__ == "__main__":
    main()