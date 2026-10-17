"""Configuración central de HERMES (rutas, parámetros y logging).

Los valores se pueden cambiar con variables de entorno (ver .env.example),
así no hay que editar el código ni guardar datos sensibles en él.
"""
import logging
import os
from pathlib import Path

from .seguridad import FiltroSecretos

RAIZ = Path(__file__).resolve().parents[1]
DATA_DIR = RAIZ / "data"
MODELS_DIR = RAIZ / "models"
LOGS_DIR = RAIZ / "logs"

DATASET = DATA_DIR / "dataset.csv"
MEDICIONES_REALES = DATA_DIR / "mediciones_reales.csv"
INTENCIONES = DATA_DIR / "intenciones.csv"
MODELO_DIAGNOSTICO = MODELS_DIR / "modelo_diagnostico.joblib"
MODELO_INTENCIONES = MODELS_DIR / "modelo_intenciones.joblib"


def _entero(nombre, defecto, minimo, maximo):
    """Lee un entero de una variable de entorno, acotado a un rango."""
    try:
        valor = int(os.environ.get(nombre, defecto))
    except ValueError:
        valor = defecto
    return max(minimo, min(maximo, valor))


HOST_PRUEBA = os.environ.get("HERMES_HOST_PRUEBA", "8.8.8.8")
NUM_PINGS = _entero("HERMES_PINGS", 5, 2, 20)
CONFIANZA_MINIMA_ML = 0.55
LONGITUD_MAXIMA_CONSULTA = 300


def configurar_logging(nivel=logging.INFO):
    """Registra eventos importantes en logs/hermes.log (y errores en consola)."""
    logger = logging.getLogger("hermes")
    if logger.handlers:
        return logger
    logger.setLevel(nivel)
    LOGS_DIR.mkdir(exist_ok=True)
    formato = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    archivo = logging.FileHandler(LOGS_DIR / "hermes.log", encoding="utf-8")
    archivo.setFormatter(formato)
    archivo.addFilter(FiltroSecretos())
    logger.addHandler(archivo)
    consola = logging.StreamHandler()
    consola.setLevel(logging.ERROR)
    consola.setFormatter(formato)
    consola.addFilter(FiltroSecretos())
    logger.addHandler(consola)
    return logger
