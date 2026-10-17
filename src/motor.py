"""Motor de HERMES: une NLP, mediciones, diagnóstico y el subsistema del router.

app.py (consola) y streamlit_app.py (web) solo muestran lo que devuelve aquí,
así la lógica vive en un único lugar.
"""
import logging
from dataclasses import asdict, dataclass, field
from typing import Optional

from . import discovery, dispositivos, network, nlp
from .diagnostico import Diagnostico, diagnosticar

log = logging.getLogger("hermes.motor")

AYUDA = (
    "No pude identificar el problema. Prueba con frases como:\n"
    "- Mi internet está lento\n- No tengo internet\n- Quiero revisar mi red\n"
    "- ¿Qué canal Wi-Fi me conviene?\n- ¿Cuántos dispositivos hay en mi red?\n"
    "- Dame información de mi router"
)
INTENCIONES_DE_RED = {"diagnostico_latencia", "diagnostico_conectividad", "diagnostico_general"}


@dataclass
class Respuesta:
    intencion: str
    mensaje: str = ""
    red: dict = field(default_factory=dict)
    medicion: Optional[network.MedicionRed] = None
    diagnostico: Optional[Diagnostico] = None
    datos: dict = field(default_factory=dict)


def _diagnostico_de_red(respuesta):
    info = discovery.obtener_informacion_red()
    respuesta.red = info
    respuesta.medicion = network.medir_red(gateway_ip=info["gateway"])
    respuesta.diagnostico = diagnosticar(respuesta.medicion)


def _analisis_wifi(respuesta):
    from .router.wifi_analyzer import WiFiAnalyzer
    analizador = WiFiAnalyzer()
    informe = analizador.analizar(analizador.escanear_redes())
    respuesta.datos = informe
    if informe["correcto"]:
        respuesta.mensaje = (
            f"Redes detectadas: {informe['cantidad_redes']}. "
            f"Canal sugerido: {informe['canal_recomendado']}. "
            "(Es una recomendación basada en redes visibles; HERMES no cambió nada en tu router.)"
        )
    else:
        respuesta.mensaje = f"No se pudo analizar el Wi-Fi: {informe['error']}"


def _listar_dispositivos(respuesta):
    lista = dispositivos.escanear()
    respuesta.datos = {"dispositivos": [asdict(d) for d in lista]}
    aleatorias = sum(d.mac_aleatoria for d in lista)
    respuesta.mensaje = (
        f"Se detectaron {len(lista)} dispositivos conectados a tu red "
        "(cuentan dispositivos, no personas)."
    )
    if aleatorias:
        respuesta.mensaje += (
            f" {aleatorias} {'usa' if aleatorias == 1 else 'usan'} dirección MAC privada/aleatoria "
            "(típico de móviles), por lo que no se puede identificar su fabricante.")


def _info_router(respuesta):
    from .router.capability_detector import RouterCapabilityDetector
    gateway = discovery.obtener_gateway()
    if not gateway:
        respuesta.mensaje = "No pude detectar la dirección de tu router."
        return
    respuesta.red = {"gateway": gateway}
    try:
        respuesta.datos = RouterCapabilityDetector(gateway).detectar()
        respuesta.mensaje = f"Router detectado en {gateway} (solo lectura, sin iniciar sesión)."
    except ValueError as error:   # gateway que no es IP privada
        respuesta.mensaje = str(error)


def procesar_consulta(texto):
    """Punto de entrada único: texto del usuario -> Respuesta."""
    intencion = nlp.identificar_intencion(texto)
    respuesta = Respuesta(intencion=intencion)
    log.info("Consulta recibida; intención=%s", intencion)
    try:
        if intencion in INTENCIONES_DE_RED:
            _diagnostico_de_red(respuesta)
        elif intencion == "analizar_wifi":
            _analisis_wifi(respuesta)
        elif intencion == "listar_dispositivos":
            _listar_dispositivos(respuesta)
        elif intencion == "info_router":
            _info_router(respuesta)
        else:
            respuesta.mensaje = AYUDA
    except Exception:
        log.exception("Error procesando la consulta")
        respuesta.mensaje = "Ocurrió un error inesperado. Revisa logs/hermes.log."
    return respuesta
