"""Diagnóstico: combina reglas claras con el modelo de ML.

Orden de decisión:
 1. Reglas de conectividad (¿llega al router? ¿sale a Internet?).
 2. Si hay conexión y datos suficientes: modelo de ML (con su confianza).
 3. Si el modelo no está disponible o duda: reglas de respaldo.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from . import config, machine_learning

log = logging.getLogger("hermes.diagnostico")

MENSAJES = {
    "estable": "La conexión parece estable.",
    "latencia_moderada": "La conexión funciona, pero presenta una latencia moderada.",
    "latencia_alta": "La latencia hacia Internet es alta.",
    "perdida_paquetes": "Se detecta una pérdida de paquetes alta.",
    "inestable": "La conexión es inestable: los tiempos de respuesta varían mucho (jitter alto).",
    "red_local_degradada": "El problema aparece ya en tu red local (entre tu equipo y el router).",
    "sin_internet": "Tu equipo llega al router, pero el router no sale a Internet.",
    "sin_red_local": "Tu equipo no logra comunicarse con el router ni con Internet.",
    "sin_conexion": "No hay conexión a Internet.",
    "sin_datos": "No fue posible completar las mediciones de red.",
}

RECOMENDACIONES = {
    "estable": "No se detectan problemas importantes. Puedes continuar usando la conexión.",
    "latencia_moderada": "Si usas Wi-Fi, acércate al router o usa cable de red. Cierra descargas en segundo plano.",
    "latencia_alta": "Comprueba si otros dispositivos saturan la red, reinicia el router y repite la prueba. Si persiste, contacta a tu proveedor.",
    "perdida_paquetes": "Revisa cables y conexión Wi-Fi, reinicia el router y prueba con otro dispositivo. Si persiste, contacta a tu proveedor.",
    "inestable": "Cambia el canal Wi-Fi (HERMES puede sugerir uno: pregunta por el Wi-Fi), aléjate de microondas o paredes gruesas, o usa cable.",
    "red_local_degradada": "El Internet no es el culpable: acércate al router, cambia el canal Wi-Fi, reinicia el router o prueba por cable.",
    "sin_internet": "Reinicia el módem/router y espera unos minutos. Si sigue igual, el problema es del proveedor: llama a soporte.",
    "sin_red_local": "Verifica que estés conectado al Wi-Fi o que el cable esté bien puesto, y que el router esté encendido.",
    "sin_conexion": "Verifica que el router esté encendido y que tu dispositivo esté conectado a la red.",
    "sin_datos": "Revisa que el comando 'ping' funcione en tu sistema y vuelve a intentar.",
}


@dataclass
class Diagnostico:
    problema: str
    mensaje: str
    recomendacion: str
    origen: str                      # "conectividad", "ml" o "reglas"
    confianza: Optional[float] = None


def clasificar_por_reglas(c):
    """Reglas de respaldo. `c` es el dict de características de la medición."""
    if c["latencia_gateway"] > 25 or c["perdida_gateway"] > 5:
        return "red_local_degradada"
    if c["perdida"] > 10:
        return "perdida_paquetes"
    if c["jitter"] > 30:
        return "inestable"
    if c["latencia"] > 100:
        return "latencia_alta"
    if c["latencia"] > 50:
        return "latencia_moderada"
    return "estable"


def _armar(problema, origen, confianza=None):
    return Diagnostico(problema, MENSAJES[problema], RECOMENDACIONES[problema], origen, confianza)


def diagnosticar(medicion, usar_ml=True):
    """Recibe una MedicionRed y devuelve un Diagnostico."""
    internet, gateway = medicion.internet, medicion.gateway

    # Si el propio comando ping falló (no existe, tiempo agotado), no hay medición
    # válida: es mejor avisarlo que culpar a la red.
    if internet.error and (gateway is None or gateway.error):
        return _armar("sin_datos", "conectividad")

    if not internet.conexion:
        if medicion.tiene_gateway and gateway.conexion:
            return _armar("sin_internet", "conectividad")
        if medicion.tiene_gateway:
            return _armar("sin_red_local", "conectividad")
        return _armar("sin_conexion", "conectividad")

    caracteristicas = medicion.caracteristicas()
    if caracteristicas is None:
        # Hay Internet pero no sabemos nada del router: reglas solo con lo medido.
        caracteristicas = {
            "latencia": internet.latencia, "perdida": internet.perdida,
            "jitter": internet.jitter, "latencia_gateway": 0.0, "perdida_gateway": 0.0,
        }
        return _armar(clasificar_por_reglas(caracteristicas), "reglas")

    if usar_ml:
        modelo = machine_learning.cargar_modelo()
        if modelo is not None:
            try:
                etiqueta, confianza = machine_learning.predecir_problema(modelo, caracteristicas)
                if confianza >= config.CONFIANZA_MINIMA_ML:
                    return _armar(etiqueta, "ml", confianza)
                log.info("Confianza del modelo baja (%.2f); se usan reglas.", confianza)
            except Exception as error:
                log.error("Falló la predicción del modelo: %s", error)

    return _armar(clasificar_por_reglas(caracteristicas), "reglas")
