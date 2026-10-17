import unittest

from src.router import registro
from src.router.registro import InfoAdaptador, conectar_router, elegir_adaptador


class TestRegistro(unittest.TestCase):
    def setUp(self):
        self._copia = list(registro._ADAPTADORES)

    def tearDown(self):
        registro._ADAPTADORES[:] = self._copia

    def test_simulacion_no_requiere_credenciales_ni_red(self):
        r = conectar_router("192.168.100.1", simulacion=True)
        self.assertTrue(r["correcto"])
        self.assertEqual(r["adaptador"], "simulado")
        self.assertIn("SIMULACIÓN", r["advertencias"][0])

    def test_elige_el_adaptador_con_mayor_puntaje(self):
        registro.registrar_adaptador(InfoAdaptador("a", lambda h: 10, None))
        registro.registrar_adaptador(InfoAdaptador("b", lambda h: 80, None))
        registro.registrar_adaptador(InfoAdaptador("c", lambda h: 0, None))
        info, puntaje = elegir_adaptador({})
        self.assertEqual((info.nombre, puntaje), ("b", 80))

    def test_sin_candidatos(self):
        registro._ADAPTADORES.clear()
        self.assertEqual(elegir_adaptador({"fabricante": "X"}), (None, 0))

    def test_router_sin_adaptador_da_mensaje_claro(self):
        registro._ADAPTADORES.clear()
        huella = {"ip": "192.168.1.1", "servicios": {"http": True, "https": False}}
        original = registro.obtener_huella
        registro.obtener_huella = lambda ip: huella
        try:
            r = conectar_router("192.168.1.1")
        finally:
            registro.obtener_huella = original
        self.assertFalse(r["correcto"])
        self.assertIn("adaptador", r["error"])

    def test_pide_credenciales_si_hay_adaptador(self):
        registro._ADAPTADORES.clear()
        registro.registrar_adaptador(InfoAdaptador("falso", lambda h: 50, None))
        huella = {"ip": "192.168.1.1", "servicios": {"http": True, "https": False}}
        original = registro.obtener_huella
        registro.obtener_huella = lambda ip: huella
        try:
            r = conectar_router("192.168.1.1")
        finally:
            registro.obtener_huella = original
        self.assertFalse(r["correcto"])
        self.assertIn("contraseña", r["error"])

    def test_no_sondea_ips_publicas(self):
        with self.assertRaises(ValueError):
            conectar_router("8.8.8.8")


if __name__ == "__main__":
    unittest.main()
