import unittest

from src.politicas import GuardianRouter, Modo
from src.router.adapters.simulado import RouterSimulado
from src.router.manager import RouterManager

PROPIO, TV, CONSOLA, DESCONOCIDO = ("AA:BB:CC:00:00:01", "AA:BB:CC:00:00:03",
                                    "AA:BB:CC:00:00:04", "AA:BB:CC:00:00:05")


class RedSana:
    def antes(self): pass
    def despues(self): return True


class RedCaida:
    def antes(self): pass
    def despues(self): return False


class Reloj:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t
    def dormir(self, s): self.t += s


def crear(modo, verificador=None, **kw):
    router = RouterSimulado()
    manager = RouterManager()
    manager.establecer_router(router)
    reloj = Reloj()
    g = GuardianRouter(manager, modo, protegidos=[PROPIO], verificador=verificador or RedSana(),
                       espera_verificacion=10, intervalo=5, reloj=reloj, dormir=reloj.dormir, **kw)
    return g, router


class TestModos(unittest.TestCase):
    def test_sugerir_no_ejecuta(self):
        g, router = crear(Modo.SUGERIR)
        r = g.ejecutar("cambiar_canal", 11, lambda t: True)
        self.assertFalse(r.ejecutada)
        self.assertEqual(router.obtener_configuracion_wifi()["canal"], 6)

    def test_confirmar_respeta_la_respuesta(self):
        g, router = crear(Modo.CONFIRMAR)
        self.assertFalse(g.ejecutar("cambiar_canal", 11, lambda t: False).ejecutada)
        self.assertEqual(router.obtener_configuracion_wifi()["canal"], 6)
        self.assertTrue(g.ejecutar("cambiar_canal", 11, lambda t: True).ejecutada)
        self.assertEqual(router.obtener_configuracion_wifi()["canal"], 11)

    def test_automatico_ejecuta_acciones_de_bajo_riesgo_sin_preguntar(self):
        g, router = crear(Modo.AUTOMATICO)
        self.assertTrue(g.ejecutar("limitar_cliente", (CONSOLA, 2000)).ejecutada)
        limite = next(c for c in router.obtener_clientes() if c["mac"] == CONSOLA)["limite_kbps"]
        self.assertEqual(limite, 2000)

    def test_automatico_no_bloquea_ni_reinicia_sin_confirmacion(self):
        g, router = crear(Modo.AUTOMATICO)
        self.assertFalse(g.ejecutar("bloquear_cliente", DESCONOCIDO).ejecutada)
        self.assertFalse(g.ejecutar("reiniciar").ejecutada)
        self.assertEqual(router.reinicios, 0)
        self.assertFalse(any(c["bloqueado"] for c in router.obtener_clientes()))


class TestProtecciones(unittest.TestCase):
    def test_no_bloquea_ni_limita_objetivos_protegidos(self):
        g, router = crear(Modo.CONFIRMAR)
        self.assertFalse(g.ejecutar("bloquear_cliente", PROPIO, lambda t: True).ejecutada)
        self.assertFalse(g.ejecutar("limitar_cliente", (PROPIO, 1000), lambda t: True).ejecutada)

    def test_no_bloquea_a_la_mitad_de_la_red(self):
        g, router = crear(Modo.CONFIRMAR, max_cambios_por_hora=10)
        # 5 clientes: se permite bloquear 2; el tercero ya sería "la mitad o más".
        self.assertTrue(g.ejecutar("bloquear_cliente", TV, lambda t: True).ejecutada)
        self.assertTrue(g.ejecutar("bloquear_cliente", CONSOLA, lambda t: True).ejecutada)
        r = g.ejecutar("bloquear_cliente", DESCONOCIDO, lambda t: True)
        self.assertFalse(r.ejecutada)
        self.assertIn("mitad", r.motivo)

    def test_limite_de_cambios_por_hora(self):
        g, _ = crear(Modo.AUTOMATICO, max_cambios_por_hora=2)
        self.assertTrue(g.ejecutar("cambiar_canal", 1).ejecutada)
        self.assertTrue(g.ejecutar("cambiar_canal", 11).ejecutada)
        r = g.ejecutar("cambiar_canal", 6)
        self.assertFalse(r.ejecutada)
        self.assertIn("por hora", r.motivo)

    def test_el_limite_se_libera_con_el_tiempo(self):
        g, _ = crear(Modo.AUTOMATICO, max_cambios_por_hora=1)
        g.ejecutar("cambiar_canal", 1)
        self.assertFalse(g.ejecutar("cambiar_canal", 11).ejecutada)
        g._reloj.t += 3601
        self.assertTrue(g.ejecutar("cambiar_canal", 11).ejecutada)

    def test_valores_invalidos_se_rechazan(self):
        g, _ = crear(Modo.AUTOMATICO)
        with self.assertRaises(ValueError):
            g.ejecutar("cambiar_canal", 99)


class TestReversion(unittest.TestCase):
    def test_cambio_de_canal_se_revierte_si_la_red_cae(self):
        g, router = crear(Modo.AUTOMATICO, verificador=RedCaida())
        r = g.ejecutar("cambiar_canal", 11)
        self.assertTrue(r.revertida)
        self.assertEqual(router.obtener_configuracion_wifi()["canal"], 6)

    def test_bloqueo_se_revierte(self):
        g, router = crear(Modo.CONFIRMAR, verificador=RedCaida())
        r = g.ejecutar("bloquear_cliente", TV, lambda t: True)
        self.assertTrue(r.revertida)
        self.assertFalse(next(c for c in router.obtener_clientes() if c["mac"] == TV)["bloqueado"])

    def test_limite_previo_se_restaura(self):
        g, router = crear(Modo.AUTOMATICO)
        g.ejecutar("limitar_cliente", (CONSOLA, 5000))
        g.verificador = RedCaida()
        r = g.ejecutar("limitar_cliente", (CONSOLA, 500))
        self.assertTrue(r.revertida)
        self.assertEqual(next(c for c in router.obtener_clientes() if c["mac"] == CONSOLA)["limite_kbps"], 5000)

    def test_espera_hasta_que_la_red_se_recupera(self):
        class SeRecupera(RedSana):
            def __init__(self): self.n = 0
            def despues(self):
                self.n += 1
                return self.n >= 2
        g, router = crear(Modo.AUTOMATICO, verificador=SeRecupera())
        r = g.ejecutar("cambiar_canal", 11)
        self.assertFalse(r.revertida)
        self.assertEqual(router.obtener_configuracion_wifi()["canal"], 11)


if __name__ == "__main__":
    unittest.main()
