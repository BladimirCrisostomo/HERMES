"""Genera un dataset SINTÉTICO de entrenamiento (data/dataset.csv).

Uso:  python -m scripts.generar_dataset

Cada clase se muestrea con distribuciones que se solapan entre sí (no con
umbrales exactos), para que el modelo aprenda fronteras estadísticas y no
simplemente copie las reglas de diagnostico.py.

IMPORTANTE: es una base para arrancar. Para que el modelo refleje TU red,
agrega mediciones reales con `python -m scripts.registrar_medicion`.
"""
import numpy as np
import pandas as pd

from src import config

CLASES = [
    "estable", "latencia_moderada", "latencia_alta",
    "perdida_paquetes", "inestable", "red_local_degradada",
]
COLUMNAS = ["latencia", "perdida", "jitter", "latencia_gateway", "perdida_gateway"]


def _fila(clase, rng):
    gw_lat = abs(rng.normal(3, 1.5)) + 1      # un router sano responde en pocos ms
    gw_loss = 0.0
    loss = rng.choice([0.0, rng.uniform(0, 2)], p=[0.85, 0.15])
    jitter = abs(rng.normal(4, 3))

    if clase == "estable":
        lat = float(np.clip(rng.normal(30, 12), 5, 62))
    elif clase == "latencia_moderada":
        lat = float(np.clip(rng.normal(80, 15), 48, 115))
        jitter = abs(rng.normal(9, 5))
    elif clase == "latencia_alta":
        lat = float(np.clip(rng.normal(230, 90), 98, 900))
        loss = rng.uniform(0, 5)
        jitter = abs(rng.normal(20, 15))
    elif clase == "perdida_paquetes":
        lat = float(np.clip(rng.normal(60, 40), 10, 400))
        loss = rng.uniform(8, 60)
        jitter = abs(rng.normal(15, 10))
    elif clase == "inestable":
        lat = float(np.clip(rng.normal(70, 30), 15, 300))
        loss = rng.uniform(0, 8)
        jitter = rng.uniform(28, 150)
    else:  # red_local_degradada: el problema ya aparece al llegar al router
        if rng.random() < 0.7:
            gw_lat = rng.uniform(22, 300)
        else:
            gw_lat = abs(rng.normal(8, 4)) + 2
            gw_loss = rng.uniform(5, 40)
        lat = gw_lat + abs(rng.normal(35, 20))
        loss = rng.uniform(0, 25)
        jitter = abs(rng.normal(25, 20))

    return [round(lat, 1), round(float(loss), 1), round(float(jitter), 1),
            round(float(gw_lat), 1), round(float(gw_loss), 1), clase]


def generar(por_clase=250, semilla=42):
    rng = np.random.default_rng(semilla)
    filas = [_fila(c, rng) for c in CLASES for _ in range(por_clase)]
    df = pd.DataFrame(filas, columns=COLUMNAS + ["problema"])
    return df.sample(frac=1, random_state=semilla).reset_index(drop=True)


if __name__ == "__main__":
    df = generar()
    config.DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(config.DATASET, index=False)
    print(f"Dataset guardado en {config.DATASET} ({len(df)} filas)")
    print(df["problema"].value_counts().to_string())
