import unittest

from src.router import web_info
from src.router.detector import RouterDetector
from src.router.interface import RouterController, RouterReader
from src.router.manager import RouterManager


class RouterFalso(RouterController):
    def __init__(self):
        self.llamadas = []

    def conectar(self): pass
    def desconectar(self): pass
    def obtener_informacion(self): return {}
    def obtener_capacidades(self): return {}
    def obtener_clientes(self): return []
    def obtener_configuracion_wifi(self): return {}
    def cambiar_canal(self, canal): self.llamadas.append(("canal", canal))
    def bloquear_cliente(self, mac): self.llamadas.append(("bloquear", mac))
    def desbloquear_cliente(self, mac): self.llamadas.append(("desbloquear", mac))
    def limitar_cliente(self, mac, kbps): self.llamadas.append(("limitar", mac, kbps))
    def quitar_limite(self, mac): self.llamadas.append(("quitar_limite", mac))
    def reiniciar(self): self.llamadas.append(("reiniciar",))


class LectorFalso(RouterReader):
    def conectar(self): pass
    def desconectar(self): pass
    def obtener_informacion(self): return {}
    def obtener_capacidades(self): return {}
    def obtener_clientes(self): return []
    def obtener_configuracion_wifi(self): return {}


def manager(router, capacidades=None):
    m = RouterManager()
    m.establecer_router(router, capacidades)
    return m


class TestAcciones(unittest.TestCase):
    CAPS = {"cambiar_canal_wifi": "confirmada", "bloquear_cliente": "confirmada",
            "limitar_cliente": "confirmada", "reiniciar": "confirmada"}
    MAC = "AA:BB:CC:00:00:03"

    def test_limitar_pasa_mac_y_velocidad(self):
        r = RouterFalso()
        res = manager(r, self.CAPS).ejecutar_accion("limitar_cliente", (self.MAC, 2000), lambda t: True)
        self.assertTrue(res["correcto"])
        self.assertEqual(r.llamadas, [("limitar", self.MAC, 2000)])

    def test_reiniciar_siempre_pide_confirmacion(self):
        r = RouterFalso()
        manager(r, self.CAPS).ejecutar_accion("reiniciar", None, lambda t: False)
        self.assertEqual(r.llamadas, [])

    def test_limites_invalidos(self):
        m = manager(RouterFalso(), self.CAPS)
        for valor in [(self.MAC, 1), (self.MAC, 10**9), (self.MAC, "5"), (self.MAC,), "x"]:
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    m.ejecutar_accion("limitar_cliente", valor, lambda t: True)

    def test_capacidades_se_toman_del_adaptador(self):
        from src.router.adapters.simulado import RouterSimulado
        m = RouterManager()
        m.establecer_router(RouterSimulado())
        self.assertEqual(m.capacidades["bloquear_cliente"], "confirmada")

    def test_sin_confirmacion_no_se_ejecuta(self):
        r = RouterFalso()
        res = manager(r, self.CAPS).ejecutar_accion("cambiar_canal", 6, lambda t: False)
        self.assertFalse(res["correcto"])
        self.assertEqual(r.llamadas, [])

    def test_con_confirmacion_se_ejecuta(self):
        r = RouterFalso()
        res = manager(r, self.CAPS).ejecutar_accion("cambiar_canal", 6, lambda t: True)
        self.assertTrue(res["correcto"])
        self.assertEqual(r.llamadas, [("canal", 6)])

    def test_capacidad_no_confirmada_bloquea_la_accion(self):
        r = RouterFalso()
        res = manager(r, {"cambiar_canal_wifi": "no_verificada"}).ejecutar_accion(
            "cambiar_canal", 6, lambda t: True)
        self.assertFalse(res["correcto"])
        self.assertEqual(r.llamadas, [])

    def test_adaptador_de_solo_lectura_no_puede_modificar(self):
        res = manager(LectorFalso(), self.CAPS).ejecutar_accion("cambiar_canal", 6, lambda t: True)
        self.assertFalse(res["correcto"])

    def test_valores_invalidos(self):
        m = manager(RouterFalso(), self.CAPS)
        for accion, valor in [("cambiar_canal", 99), ("cambiar_canal", "6"),
                              ("bloquear_cliente", "no-es-mac"), ("reiniciar", 5)]:
            with self.subTest(accion=accion, valor=valor):
                with self.assertRaises(ValueError):
                    m.ejecutar_accion(accion, valor, lambda t: True)

    def test_accion_desconocida(self):
        with self.assertRaises(ValueError):
            manager(RouterFalso()).ejecutar_accion("formatear", 1, lambda t: True)

    def test_lector_no_es_controlador(self):
        self.assertFalse(issubclass(RouterReader, RouterController))


class TestDeteccion(unittest.TestCase):
    def test_solo_ips_privadas(self):
        with self.assertRaises(ValueError):
            RouterDetector("8.8.8.8")

    def test_puerto_cerrado(self):
        self.assertFalse(RouterDetector("127.0.0.1").comprobar_puerto(1, timeout=0.2))

    def test_extraccion_html(self):
        html = '<html><title> Mercusys </title><a href="/admin/login.asp">MERCUSYS</a></html>'
        self.assertEqual(web_info.obtener_titulo(html), "Mercusys")
        self.assertEqual(web_info.obtener_ruta_login(html), "/admin/login.asp")
        self.assertEqual(web_info.detectar_fabricante(html), "MERCUSYS")


if __name__ == "__main__":
    unittest.main()
