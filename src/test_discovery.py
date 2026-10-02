from discovery import obtener_informacion_red


def main():
    informacion = obtener_informacion_red()

    print("=== DESCUBRIMIENTO DE RED ===")
    print(f"Equipo: {informacion['equipo']}")
    print(f"IP local: {informacion['ip_local']}")
    print(f"Gateway: {informacion['gateway']}")


if __name__ == "__main__":
    main()