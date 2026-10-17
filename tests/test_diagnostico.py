import unittest

from src.diagnostico import clasificar_por_reglas, diagnosticar
from src.network import MedicionRed, ResultadoPing


def medicion(internet=None, gateway=None, n=5):
    """Crea una medición. Cada lista es de tiempos (ms); None = sin respuesta."""
    i = ResultadoPing("8.8.8.8", n, internet or [])
    g = None if gateway is None else ResultadoPing("192.168.1.1", n, gateway)
    return MedicionRed(i, "192.168.1.1" if g else None, g)


class TestConectividad(unittest.TestCase):
    def test_sin_internet_pero_router_responde(self):
        d = diagnosticar(medicion([], [2.0] * 5))
        self.assertEqual(d.problema, "sin_internet")

    def test_sin_router_ni_internet(self):
        d = diagnosticar(medicion([], []))
        self.assertEqual(d.problema, "sin_red_local")

    def test_sin_conexion_y_sin_gateway_conocido(self):
        d = diagnosticar(medicion([]))
        self.assertEqual(d.problema, "sin_conexion")

    def test_ping_no_disponible_no_se_confunde_con_red_caida(self):
        i = ResultadoPing("8.8.8.8", 5, error="ping no disponible")
        g = ResultadoPing("192.168.1.1", 5, error="ping no disponible")
        d = diagnosticar(MedicionRed(i, "192.168.1.1", g))
        self.assertEqual(d.problema, "sin_datos")

    def test_no_se_rompe_con_valores_ausentes(self):
        # Antes recomendar() lanzaba TypeError cuando la latencia era None.
        d = diagnosticar(medicion([]))
        self.assertTrue(d.recomendacion)


class TestReglas(unittest.TestCase):
    base = dict(latencia=30, perdida=0, jitter=3, latencia_gateway=2, perdida_gateway=0)

    def caso(self, **cambios):
        return clasificar_por_reglas({**self.base, **cambios})

    def test_estable(self):
        self.assertEqual(self.caso(), "estable")

    def test_umbrales(self):
        self.assertEqual(self.caso(latencia=75), "latencia_moderada")
        self.assertEqual(self.caso(latencia=150), "latencia_alta")
        self.assertEqual(self.caso(perdida=15), "perdida_paquetes")
        self.assertEqual(self.caso(jitter=60), "inestable")

    def test_problema_local_tiene_prioridad(self):
        self.assertEqual(self.caso(latencia=300, latencia_gateway=80), "red_local_degradada")

    def test_perdida_tiene_prioridad_sobre_latencia(self):
        self.assertEqual(self.caso(latencia=300, perdida=20), "perdida_paquetes")


class TestConML(unittest.TestCase):
    def test_ml_detecta_casos_claros(self):
        casos = [
            (medicion([25.0] * 5, [2.0] * 5), "estable"),
            (medicion([300.0, 280.0, 320.0, 310.0, 290.0], [2.0] * 5), "latencia_alta"),
            (medicion([40.0, 40.0], [2.0] * 5), "perdida_paquetes"),   # 3 de 5 perdidos
            (medicion([60.0] * 5, [150.0] * 5), "red_local_degradada"),
        ]
        for m, esperado in casos:
            with self.subTest(esperado=esperado):
                d = diagnosticar(m)
                self.assertEqual(d.problema, esperado)
                self.assertIn(d.origen, ("ml", "reglas"))

    def test_sin_ml_usa_reglas(self):
        d = diagnosticar(medicion([25.0] * 5, [2.0] * 5), usar_ml=False)
        self.assertEqual((d.problema, d.origen), ("estable", "reglas"))


if __name__ == "__main__":
    unittest.main()
