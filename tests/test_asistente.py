import unittest

from src import asistente
from src.asistente import LimitadorIntentos, atender, conectar, ejecutar, interpretar_orden, requiere_confirmacion
from src.politicas import Modo

CLIENTES = [
    {"mac": "AA:BB:CC:00:00:01", "ip": "192.168.1.101", "nombre": "laptop-jose"},
    {"mac": "AA:BB:CC:00:00:03", "ip": "192.168.1.103", "nombre": "NOVA-X6-Pro-5G"},
    {"mac": "AA:BB:CC:00:00:04", "ip": "192.168.1.104", "nombre": "smart-tv"},
    {"mac": "AA:BB:CC:00:00:05", "ip": "192.168.1.105", "nombre": "tv-sala"},
]


def orden(texto):
    return interpretar_orden(texto, CLIENTES)


class TestOrdenes(unittest.TestCase):
    def test_bloquear_por_nombre_parcial(self):
        o = orden("bloquea el nova por favor")
        self.assertEqual((o.accion, o.valor), ("bloquear_cliente", "AA:BB:CC:00:00:03"))

    def test_desbloquear_no_se_confunde_con_bloquear(self):
        self.assertEqual(orden("desbloquea a nova x6").accion, "desbloquear_cliente")

    def test_por_ip_y_por_mac(self):
        self.assertEqual(orden("bloquea la 192.168.1.104").valor, "AA:BB:CC:00:00:04")
        self.assertEqual(orden("bloquea aa-bb-cc-00-00-03").valor, "AA:BB:CC:00:00:03")

    def test_nombre_ambiguo_pide_aclaracion(self):
        o = orden("bloquea la tv")
        self.assertIsNone(o.accion)
        self.assertIn("¿A cuál", o.error)

    def test_dispositivo_desconocido(self):
        self.assertIn("No encontré", orden("bloquea la impresora").error)

    def test_nunca_bloquea_a_todos(self):
        self.assertIn("todos a la vez", orden("bloquea a todos").error)

    def test_cambiar_canal(self):
        self.assertEqual((orden("cambia el canal a 6").accion, orden("cambia el canal a 6").valor),
                         ("cambiar_canal", 6))
        self.assertEqual(orden("pon el canal en automatico").valor, 0)
        self.assertIn("¿A qué canal?", orden("cambia el canal").error)
        self.assertIn("1 al 13", orden("cambia el canal a 99").error)

    def test_preguntas_normales_no_son_ordenes(self):
        for t in ["que canal me conviene", "mi internet esta lento", "cuantos dispositivos hay", "hola"]:
            with self.subTest(t=t):
                self.assertIsNone(orden(t))


class TestLimitador(unittest.TestCase):
    def test_bloquea_tras_los_fallos_y_se_libera(self):
        t = [0.0]
        lim = LimitadorIntentos(maximo=3, espera=30, reloj=lambda: t[0])
        for _ in range(3):
            self.assertTrue(lim.puede_intentar())
            lim.registrar_fallo()
        self.assertFalse(lim.puede_intentar())
        self.assertEqual(lim.segundos_restantes(), 30)
        t[0] = 31
        self.assertTrue(lim.puede_intentar())

    def test_el_exito_reinicia_la_cuenta(self):
        lim = LimitadorIntentos(maximo=2)
        lim.registrar_fallo()
        lim.registrar_exito()
        lim.registrar_fallo()
        self.assertTrue(lim.puede_intentar())


class TestSesion(unittest.TestCase):
    def sesion(self, modo=Modo.CONFIRMAR):
        s, error, diag = conectar("192.168.100.1", simulacion=True, modo=modo)
        self.assertIsNone(error)
        return s

    def test_conectar_simulacion(self):
        s = self.sesion()
        self.assertTrue(s.simulado)
        self.assertEqual(len(s.clientes()), 5)

    def test_ip_publica_se_rechaza(self):
        s, error, _ = conectar("8.8.8.8", "x")
        self.assertIsNone(s)
        self.assertIn("red local", error)

    def test_equipo_no_compatible_explica_que_es_y_que_hacer(self):
        from src.router import registro
        original = registro.obtener_huella
        registro.obtener_huella = lambda ip: {"ip": ip, "servicios": {"http": True, "https": False},
                                              "servidor": "ModemISP/1.0", "titulo": "Panel del proveedor",
                                              "protocolo_panel": False}
        try:
            s, error, _ = conectar("192.168.100.1", "alguna-clave")
        finally:
            registro.obtener_huella = original
        self.assertIsNone(s)
        self.assertIn("ModemISP/1.0", error)
        self.assertIn("módem de tu proveedor", error)
        self.assertIn("BUSCAR MI ROUTER", error)

    def test_contrasena_incorrecta_devuelve_el_diagnostico_del_unico_intento(self):
        from src.router import registro
        from src.router.adapters.mercusys_mw306r import MercusysMW306R
        from tests.test_mercusys import RouterFalso
        falso = RouterFalso(password="la-correcta")
        originales = (registro.obtener_huella, registro.MercusysMW306R)
        registro.obtener_huella = lambda ip: {"ip": ip, "servicios": {"http": True, "https": False},
                                              "protocolo_panel": True}
        registro.MercusysMW306R = lambda ip, cred: MercusysMW306R(ip, cred, transporte=falso.transporte)
        try:
            s, error, diag = conectar("192.168.1.1", "una-incorrecta")
        finally:
            registro.obtener_huella, registro.MercusysMW306R = originales
        self.assertIsNone(s)
        self.assertIn("rechazó", error)
        self.assertEqual(diag["2_login"]["http"], 401)
        self.assertEqual(falso.intentos_login, 1)

    def test_requiere_confirmacion_segun_el_modo(self):
        s = self.sesion(Modo.CONFIRMAR)
        self.assertTrue(requiere_confirmacion(s, "cambiar_canal"))
        s.guardian.modo = Modo.AUTOMATICO
        self.assertFalse(requiere_confirmacion(s, "cambiar_canal"))
        self.assertTrue(requiere_confirmacion(s, "bloquear_cliente"))
        s.guardian.modo = Modo.SUGERIR
        self.assertFalse(requiere_confirmacion(s, "bloquear_cliente"))

    def test_ejecutar_respeta_la_confirmacion(self):
        s = self.sesion()
        self.assertFalse(ejecutar(s, "bloquear_cliente", "AA:BB:CC:00:00:03", confirmado=False).ejecutada)
        self.assertTrue(ejecutar(s, "bloquear_cliente", "AA:BB:CC:00:00:03", confirmado=True).ejecutada)
        self.assertTrue(next(c for c in s.clientes() if c["mac"] == "AA:BB:CC:00:00:03")["bloqueado"])

    def test_el_equipo_protegido_no_se_bloquea(self):
        s = self.sesion()
        self.assertFalse(ejecutar(s, "bloquear_cliente", "AA:BB:CC:00:00:01", confirmado=True).ejecutada)


class TestConversacion(unittest.TestCase):
    def test_orden_sin_router_pide_conectar(self):
        t = atender("bloquea el celular")
        self.assertIn("conexión con el router", t.texto)
        self.assertIsNone(t.orden)

    def test_orden_con_router_devuelve_la_accion(self):
        s, _, _ = conectar("192.168.100.1", simulacion=True)
        t = atender("bloquea la consola", s)
        self.assertEqual((t.orden.accion, t.orden.valor), ("bloquear_cliente", "AA:BB:CC:00:00:04"))

    def test_listar_con_router_usa_sus_clientes(self):
        s, _, _ = conectar("192.168.100.1", simulacion=True)
        t = atender("cuantos dispositivos hay conectados", s)
        self.assertEqual(len(t.clientes), 5)

    def test_error_de_orden_se_explica(self):
        s, _, _ = conectar("192.168.100.1", simulacion=True)
        self.assertIn("No encontré", atender("bloquea la impresora", s).texto)

    def test_consulta_vacia(self):
        self.assertIn("ninguna consulta", atender("   ").texto)


if __name__ == "__main__":
    unittest.main()
