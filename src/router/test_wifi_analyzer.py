from wifi_analyzer import WiFiAnalyzer


def main():
    analizador = WiFiAnalyzer()

    print("=== HERMES: ANALIZADOR INTELIGENTE DE WI-FI ===")
    print("\nEscaneando las redes Wi-Fi visibles...\n")

    datos = analizador.escanear_redes()

    if not datos["correcto"]:
        print("No se pudo completar el escaneo.")
        print(f"Motivo: {datos['error']}")
        return

    informe = analizador.analizar(datos)

    if not informe["correcto"]:
        print(informe["error"])
        return

    print(f"Redes detectadas: {informe['cantidad_redes']}")
    print("\n=== OCUPACIÓN POR CANAL ===")

    for canal in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13):
        cantidad = informe["redes_por_canal"][canal]
        barra = "#" * cantidad
        print(f"Canal {canal:2}: {cantidad:2} redes {barra}")

    print("\n=== RECOMENDACIÓN DE HERMES ===")
    print(f"Canal sugerido: {informe['canal_recomendado']}")
    print(f"Criterio: {informe['criterio']}")

    print(
        "\nAviso: la recomendación se basa en las redes "
        "visibles, no en una medición completa de interferencias."
    )
    print("HERMES no ha cambiado la configuración del router.")


if __name__ == "__main__":
    main()