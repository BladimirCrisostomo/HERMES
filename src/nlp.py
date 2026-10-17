"""Identificación de la intención del usuario.

Dos capas:
 1. Palabras clave (alta precisión, sin acentos ni mayúsculas, palabras completas).
 2. Si las palabras clave no deciden, un clasificador entrenado (TF-IDF + regresión
    logística) con data/intenciones.csv; solo se acepta si tiene confianza suficiente.
"""
import hashlib
import logging
import re
import unicodedata

import joblib

from . import config
from .seguridad import sanitizar_texto

log = logging.getLogger("hermes.nlp")

INTENCION_DESCONOCIDA = "intencion_desconocida"
CONFIANZA_MINIMA = 0.45

# Orden = prioridad. Las frases se comparan ya normalizadas (sin acentos).
PALABRAS_CLAVE = [
    ("diagnostico_conectividad", [
        "sin conexion", "sin internet", "no tengo internet", "no hay internet",
        "no tengo conexion", "no hay conexion", "no funciona internet",
        "se cayo", "no me conecto", "no puedo conectarme",
    ]),
    ("listar_dispositivos", [
        "cuantos usuarios", "cuantos dispositivos", "cuantas personas", "cuantos equipos",
        "dispositivos conectados", "usuarios conectados", "equipos conectados",
        "quien esta conectado", "quienes estan conectados", "quien esta usando", "quien usa",
        "que dispositivos", "lista de dispositivos",
    ]),
    ("analizar_wifi", ["wifi", "wi fi", "canal", "senal inalambrica", "interferencia"]),
    ("info_router", ["mi router", "gateway", "puerta de enlace", "modem"]),
    ("diagnostico_latencia", [
        "lento", "lenta", "lag", "latencia", "retraso", "tarda", "tardan", "ping", "se traba",
    ]),
    ("diagnostico_general", [
        "revisar mi red", "revisar mi internet", "revisar internet", "diagnostico",
        "comprobar mi red", "analiza mi red", "estado de mi red",
    ]),
]


def normalizar(texto):
    """Minúsculas, sin acentos ni signos: 'Conexión!' -> 'conexion'."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9ñ ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _por_palabras_clave(texto_normalizado):
    for intencion, frases in PALABRAS_CLAVE:
        for frase in frases:
            # \b evita que 'lag' coincida dentro de 'plaga' o 'colage'.
            if re.search(rf"\b{re.escape(frase)}\b", texto_normalizado):
                return intencion
    return None


def entrenar_clasificador():
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    datos = pd.read_csv(config.INTENCIONES)
    modelo = make_pipeline(
        TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2)),
        LogisticRegression(max_iter=1000, C=10),
    )
    modelo.fit(datos["texto"], datos["intencion"])
    return modelo


_cache = {}


def _hash_datos():
    """Huella del CSV de frases: si cambia, el modelo guardado ya no sirve."""
    return hashlib.sha1(config.INTENCIONES.read_bytes()).hexdigest()


def guardar_clasificador(modelo):
    config.MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"modelo": modelo, "hash": _hash_datos()}, config.MODELO_INTENCIONES)


def _clasificador():
    if "modelo" not in _cache:
        modelo = None
        try:
            if config.INTENCIONES.exists():
                if config.MODELO_INTENCIONES.exists():
                    paquete = joblib.load(config.MODELO_INTENCIONES)
                    if isinstance(paquete, dict) and paquete.get("hash") == _hash_datos():
                        modelo = paquete["modelo"]
                if modelo is None:     # no existe, o las frases cambiaron: reentrenar
                    modelo = entrenar_clasificador()
                    guardar_clasificador(modelo)
        except Exception as error:
            log.error("No se pudo preparar el clasificador de intenciones: %s", error)
        _cache["modelo"] = modelo
    return _cache["modelo"]


def identificar_intencion(texto):
    """Devuelve el nombre de la intención o 'intencion_desconocida'."""
    texto = sanitizar_texto(texto, config.LONGITUD_MAXIMA_CONSULTA)
    normalizado = normalizar(texto)
    if not normalizado:
        return INTENCION_DESCONOCIDA

    intencion = _por_palabras_clave(normalizado)
    if intencion:
        return intencion

    modelo = _clasificador()
    if modelo is not None:
        probabilidades = modelo.predict_proba([texto])[0]
        indice = probabilidades.argmax()
        if probabilidades[indice] >= CONFIANZA_MINIMA:
            return str(modelo.classes_[indice])
    return INTENCION_DESCONOCIDA
