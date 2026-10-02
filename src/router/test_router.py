from interface import RouterInterface


class RouterPrueba(RouterInterface):

    def conectar(self):
        print("Router conectado.")

    def desconectar(self):
        print("Router desconectado.")

    def obtener_informacion(self):
        return {
            "fabricante": "Router de prueba",
            "modelo": "HERMES-TEST"
        }

    def obtener_capacidades(self):
        return {
            "wifi": True,
            "cambiar_canal": True,
            "clientes": True,
            "bloqueo": True,
            "qos": True
        }

    def obtener_clientes(self):
        return []

    def obtener_configuracion_wifi(self):
        return {}

    def cambiar_canal(self, canal):
        print(f"Canal cambiado a {canal}.")

    def bloquear_cliente(self, identificador):
        print(f"Cliente {identificador} bloqueado.")

    def desbloquear_cliente(self, identificador):
        print(f"Cliente {identificador} desbloqueado.")

    def configurar_qos(self, configuracion):
        print("QoS configurado.")


router = RouterPrueba()

router.conectar()

print(router.obtener_informacion())
print(router.obtener_capacidades())

router.cambiar_canal(11)
router.bloquear_cliente("192.168.100.35")

router.desconectar()