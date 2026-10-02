from web_info import RouterWebInfo


def main():

    gateway = "192.168.100.1"

    router = RouterWebInfo(gateway)

    print("=== INFORMACIÓN WEB DEL ROUTER ===")

    for protocolo in ["http", "https"]:

        print(f"\n--- {protocolo.upper()} ---")

        resultado = router.consultar(protocolo)

        for clave, valor in resultado.items():
            print(f"{clave}: {valor}")


if __name__ == "__main__":
    main()