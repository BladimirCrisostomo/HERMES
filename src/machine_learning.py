"""Modelo de ML para clasificar el estado de la red (árbol de decisión).

Se eligió un árbol porque es explicable: se puede mostrar con export_text()
qué umbrales aprendió, algo útil para documentar y defender el proyecto.
"""
import json
import logging

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

from . import config

log = logging.getLogger("hermes.ml")

CARACTERISTICAS = ["latencia", "perdida", "jitter", "latencia_gateway", "perdida_gateway"]
OBJETIVO = "problema"


def cargar_datos():
    """Dataset base + mediciones reales (si existen)."""
    datos = pd.read_csv(config.DATASET)
    if config.MEDICIONES_REALES.exists():
        reales = pd.read_csv(config.MEDICIONES_REALES)
        datos = pd.concat([datos, reales[CARACTERISTICAS + [OBJETIVO]]], ignore_index=True)
    faltan = set(CARACTERISTICAS + [OBJETIVO]) - set(datos.columns)
    if faltan:
        raise ValueError(f"Al dataset le faltan columnas: {sorted(faltan)}")
    return datos.dropna(subset=CARACTERISTICAS + [OBJETIVO])


def _crear_modelo():
    # max_depth y min_samples_leaf evitan que el árbol memorice los datos.
    return DecisionTreeClassifier(max_depth=6, min_samples_leaf=5, random_state=42)


def entrenar_modelo(datos=None):
    """Entrena con todos los datos y devuelve (modelo, métricas)."""
    datos = cargar_datos() if datos is None else datos
    X, y = datos[CARACTERISTICAS], datos[OBJETIVO]

    # Evaluación honesta: validación cruzada + conjunto de prueba separado.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_acc = cross_val_score(_crear_modelo(), X, y, cv=cv)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    prueba = _crear_modelo().fit(X_tr, y_tr)
    pred = prueba.predict(X_te)
    clases = sorted(y.unique())

    metricas = {
        "filas": int(len(datos)),
        "accuracy_cv_media": round(float(cv_acc.mean()), 3),
        "accuracy_cv_desviacion": round(float(cv_acc.std()), 3),
        "accuracy_prueba": round(float((pred == y_te).mean()), 3),
        "clases": clases,
        "matriz_confusion": confusion_matrix(y_te, pred, labels=clases).tolist(),
        "reporte": classification_report(y_te, pred, output_dict=True, zero_division=0),
    }
    modelo = _crear_modelo().fit(X, y)
    return modelo, metricas


def guardar_modelo(modelo, metricas):
    config.MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"modelo": modelo, "caracteristicas": CARACTERISTICAS}, config.MODELO_DIAGNOSTICO)
    ruta_metricas = config.MODELO_DIAGNOSTICO.with_suffix(".json")
    ruta_metricas.write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")


_cache = {}


def cargar_modelo(entrenar_si_falta=True):
    """Carga el modelo guardado; si no existe lo entrena (tarda menos de 1 s)."""
    if "modelo" in _cache:
        return _cache["modelo"]
    modelo = None
    try:
        if config.MODELO_DIAGNOSTICO.exists():
            paquete = joblib.load(config.MODELO_DIAGNOSTICO)
            if paquete.get("caracteristicas") == CARACTERISTICAS:
                modelo = paquete["modelo"]
        if modelo is None and entrenar_si_falta and config.DATASET.exists():
            log.info("Entrenando modelo de diagnóstico (no había uno guardado).")
            modelo, metricas = entrenar_modelo()
            guardar_modelo(modelo, metricas)
    except Exception as error:  # modelo corrupto o versión de sklearn distinta
        log.error("No se pudo cargar/entrenar el modelo: %s", error)
        modelo = None
    _cache["modelo"] = modelo
    return modelo


def predecir_problema(modelo, caracteristicas):
    """Devuelve (etiqueta, confianza). `caracteristicas` es un dict."""
    fila = pd.DataFrame([[caracteristicas[c] for c in CARACTERISTICAS]], columns=CARACTERISTICAS)
    probabilidades = modelo.predict_proba(fila)[0]
    indice = probabilidades.argmax()
    return str(modelo.classes_[indice]), float(probabilidades[indice])


def explicar_modelo(modelo):
    """Reglas aprendidas por el árbol, en texto legible."""
    return export_text(modelo, feature_names=CARACTERISTICAS)
