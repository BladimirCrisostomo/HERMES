"""Agrega una medición REAL etiquetada a data/mediciones_reales.csv.

Uso:  python -m scripts.registrar_medicion

Provoca una situación (alejarte del router, descargar algo grande, desconectar
el cable...), ejecuta el script y elige qué estaba pasando. Con 50-100 mediciones
reales el modelo se adapta a tu red y la presentación gana mucho valor.
"""
import csv

from src import config, discovery, machine_learning as ml, network

ETIQUETAS = [
    "estable", "latencia_moderada", "latencia_alta",
    "perdida_paquetes", "inestable", "red_local_degradada",
]


def main():
    gateway = discovery.obtener_gateway()
    print(f"Gateway: {gateway}\nMidiendo...")
    medicion = network.medir_red(gateway_ip=gateway)
    c = medicion.caracteristicas()
    if c is None:
        print("No se pudo medir Internet y gateway a la vez; no se guardó nada.")
        return
    print("Medición:", c)
    for i, etiqueta in enumerate(ETIQUETAS, 1):
        print(f"  {i}. {etiqueta}")
    try:
        eleccion = ETIQUETAS[int(input("¿Qué estaba pasando realmente? (número): ")) - 1]
    except (ValueError, IndexError):
        print("Opción no válida; no se guardó nada.")
        return

    nuevo = not config.MEDICIONES_REALES.exists()
    with open(config.MEDICIONES_REALES, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        if nuevo:
            escritor.writerow(ml.CARACTERISTICAS + [ml.OBJETIVO])
        escritor.writerow([c[k] for k in ml.CARACTERISTICAS] + [eleccion])
    print(f"Guardado como '{eleccion}'. Reentrena con: python -m scripts.entrenar")


if __name__ == "__main__":
    main()
