import unittest

from src.network import MedicionRed, ResultadoPing, hacer_ping, parsear_ping

WINDOWS_ES = """Haciendo ping a 8.8.8.8 con 32 bytes de datos:
Respuesta desde 8.8.8.8: bytes=32 tiempo=15ms TTL=117
Respuesta desde 8.8.8.8: bytes=32 tiempo<1m TTL=117
Tiempo de espera agotado para esta solicitud.
Respuesta desde 8.8.8.8: bytes=32 tiempo=17ms TTL=117
"""
WINDOWS_EN = """Pinging 8.8.8.8 with 32 bytes of data:
Reply from 8.8.8.8: bytes=32 time=20ms TTL=117
Reply from 8.8.8.8: bytes=32 time=30ms TTL=117
"""
LINUX = """64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=10.2 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=12.4 ms
"""
INALCANZABLE = """Respuesta desde 192.168.1.50: Host de destino inaccesible.
Respuesta desde 192.168.1.50: Host de destino inaccesible.
"""


class TestParseoPing(unittest.TestCase):
    def test_windows_espanol(self):
        r = parsear_ping(WINDOWS_ES, "8.8.8.8", 4)
        self.assertEqual(r.recibidos, 3)
        self.assertEqual(r.perdida, 25.0)
        self.assertEqual(r.latencia, 11.0)
        self.assertTrue(r.conexion)

    def test_windows_ingles(self):
        r = parsear_ping(WINDOWS_EN, "8.8.8.8", 2)
        self.assertEqual((r.latencia, r.perdida, r.jitter), (25.0, 0.0, 5.0))

    def test_linux_con_decimales(self):
        r = parsear_ping(LINUX, "8.8.8.8", 2)
        self.assertEqual(r.latencia, 11.3)

    def test_sin_respuestas_es_perdida_total(self):
        r = parsear_ping(INALCANZABLE, "192.168.1.50", 2)
        self.assertFalse(r.conexion)
        self.assertEqual(r.perdida, 100.0)
        self.assertIsNone(r.latencia)

    def test_salida_vacia_no_rompe(self):
        r = parsear_ping("", "8.8.8.8", 4)
        self.assertEqual(r.perdida, 100.0)

    def test_hacer_ping_rechaza_host_peligroso(self):
        with self.assertRaises(ValueError):
            hacer_ping("-f", 2)


class TestMedicion(unittest.TestCase):
    def test_caracteristicas_requieren_gateway(self):
        internet = ResultadoPing("8.8.8.8", 2, [20.0, 22.0])
        self.assertIsNone(MedicionRed(internet).caracteristicas())

    def test_caracteristicas_completas(self):
        internet = ResultadoPing("8.8.8.8", 2, [20.0, 22.0])
        gw = ResultadoPing("192.168.1.1", 2, [2.0, 3.0])
        c = MedicionRed(internet, "192.168.1.1", gw).caracteristicas()
        self.assertEqual(c["latencia"], 21.0)
        self.assertEqual(c["latencia_gateway"], 2.5)


if __name__ == "__main__":
    unittest.main()
