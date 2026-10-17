"""Entrena y guarda los modelos de HERMES, y muestra qué tan bien funcionan.

Uso:  python -m scripts.entrenar
"""
from src import config, machine_learning as ml, nlp


def main():
    print("=== Modelo de diagnóstico ===")
    modelo, m = ml.entrenar_modelo()
    ml.guardar_modelo(modelo, m)
    print(f"Filas de entrenamiento: {m['filas']}")
    print(f"Accuracy (validación cruzada 5 folds): {m['accuracy_cv_media']} ± {m['accuracy_cv_desviacion']}")
    print(f"Accuracy (conjunto de prueba):         {m['accuracy_prueba']}")
    print("\nMatriz de confusión (filas = real, columnas = predicho):")
    print("Clases:", m["clases"])
    for clase, fila in zip(m["clases"], m["matriz_confusion"]):
        print(f"  {clase:22} {fila}")
    print("\nReglas aprendidas por el árbol:\n")
    print(ml.explicar_modelo(modelo))
    print(f"Modelo guardado en {config.MODELO_DIAGNOSTICO}")

    print("\n=== Clasificador de intenciones ===")
    clasificador = nlp.entrenar_clasificador()
    nlp.guardar_clasificador(clasificador)
    print(f"Modelo guardado en {config.MODELO_INTENCIONES}")


if __name__ == "__main__":
    main()
