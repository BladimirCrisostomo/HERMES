
from detector import RouterDetector
from web_info import RouterWebInfo


class RouterCapabilityDetector:
    """
    Investiga qué funciones del router están confirmadas,
    cuáles tienen indicios y cuáles siguen sin verificarse.
    """

    def __init__(self, ip):
        self.ip = ip
        self.detector = RouterDetector(ip)
        self.web = RouterWebInfo(ip)

    def detectar(self):
        """
        Recopila evidencias sin modificar la configuración.
        """

        resultado = {
            "ip": self.ip,
            "capacidades": {},
            "evidencias": {},
            "informacion": {}
        }

        # 1. Comprobar los puertos de administración conocidos.
        servicios = self.detector.detectar_servicios()

        resultado["evidencias"]["puertos"] = servicios

        # 2. Investigar HTTP si el puerto está disponible.
        if servicios.get("http"):
            datos_http = self.web.consultar("http")

            if "error" not in datos_http:
                resultado["capacidades"]["administracion_http"] = (
                    "confirmada"
                )

                resultado["informacion"]["servidor_web"] = (
                    datos_http.get("servidor")
                )

                resultado["informacion"]["fabricante_detectado"] = (
                    datos_http.get("fabricante_detectado")
                )

                resultado["informacion"]["ruta_login"] = (
                    datos_http.get("ruta_login")
                )

                resultado["evidencias"]["http"] = {
                    "codigo": datos_http.get("codigo"),
                    "servidor": datos_http.get("servidor")
                }

            else:
                resultado["capacidades"]["administracion_http"] = (
                    "no_confirmada"
                )

                resultado["evidencias"]["http"] = {
                    "error": datos_http["error"]
                }

        else:
            resultado["capacidades"]["administracion_http"] = (
                "no_detectada"
            )

        # 3. Investigar HTTPS si el puerto está disponible.
        if servicios.get("https"):
            datos_https = self.web.consultar("https")

            if "error" not in datos_https:
                resultado["capacidades"]["administracion_https"] = (
                    "confirmada"
                )

                resultado["evidencias"]["https"] = {
                    "codigo": datos_https.get("codigo")
                }

            else:
                # El puerto responde, pero la consulta HTTPS falló.
                # No afirmamos que HTTPS esté desactivado.
                resultado["capacidades"]["administracion_https"] = (
                    "no_verificada"
                )

                resultado["evidencias"]["https"] = {
                    "error": datos_https["error"],
                    "nota": (
                        "El puerto responde, pero la consulta "
                        "HTTPS no pudo completarse."
                    )
                }

        else:
            resultado["capacidades"]["administracion_https"] = (
                "no_detectada"
            )

        # 4. Estas funciones requieren evidencia adicional.
        # No asumimos que existen solo porque haya una web.
        funciones_por_verificar = [
            "obtener_clientes",
            "cambiar_canal_wifi",
            "bloquear_cliente",
            "configurar_qos"
        ]

        for funcion in funciones_por_verificar:
            resultado["capacidades"][funcion] = "no_verificada"

        return resultado

    def mostrar(self):
        """
        Presenta los resultados en la terminal.
        """

        resultado = self.detectar()

        print("=== DETECTOR DE CAPACIDADES DE HERMES ===")
        print(f"Router: {resultado['ip']}")

        print("\n--- INFORMACIÓN DETECTADA ---")

        for nombre, valor in resultado["informacion"].items():
            print(f"{nombre}: {valor}")

        print("\n--- CAPACIDADES ---")

        for nombre, estado in resultado["capacidades"].items():
            print(f"{nombre}: {estado}")

        print("\n--- EVIDENCIAS DE RED ---")

        for nombre, evidencia in resultado["evidencias"].items():
            print(f"{nombre}: {evidencia}")

        return resultado
