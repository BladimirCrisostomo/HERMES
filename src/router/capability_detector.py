"""Investiga qué funciones del router están confirmadas y cuáles no.

Solo recopila evidencias; no modifica nada en el router.
"""
from . import capabilities as cap
from .detector import RouterDetector
from .web_info import RouterWebInfo


class RouterCapabilityDetector:
    def __init__(self, ip):
        self.ip = ip
        self.detector = RouterDetector(ip)
        self.web = RouterWebInfo(ip)

    def _probar_web(self, protocolo, servicios, resultado):
        nombre = f"administracion_{protocolo}"
        if not servicios.get(protocolo):
            resultado["capacidades"][nombre] = cap.NO_DETECTADA
            return
        datos = self.web.consultar(protocolo)
        if "error" in datos:
            # El puerto responde pero la consulta falló: no afirmamos nada más.
            resultado["capacidades"][nombre] = cap.NO_VERIFICADA
            resultado["evidencias"][protocolo] = {"error": datos["error"]}
            return
        resultado["capacidades"][nombre] = cap.CONFIRMADA
        resultado["evidencias"][protocolo] = {
            "codigo": datos["codigo"], "servidor": datos["servidor"],
        }
        if protocolo == "http":
            resultado["informacion"].update({
                "servidor_web": datos["servidor"],
                "fabricante_detectado": datos["fabricante_detectado"],
                "ruta_login": datos["ruta_login"],
            })

    def detectar(self):
        servicios = self.detector.detectar_servicios()
        resultado = {
            "ip": self.ip, "capacidades": {}, "informacion": {},
            "evidencias": {"puertos": servicios},
        }
        for protocolo in ("http", "https"):
            self._probar_web(protocolo, servicios, resultado)
        for funcion in cap.FUNCIONES_POR_VERIFICAR:
            resultado["capacidades"][funcion] = cap.NO_VERIFICADA
        return resultado
