import unittest

from src.nlp import identificar_intencion as intencion, normalizar


class TestNLP(unittest.TestCase):
    def test_normalizar(self):
        self.assertEqual(normalizar("¡Conexión   CAÍDA!"), "conexion caida")

    def test_casos_basicos(self):
        casos = {
            "Mi Internet está muy lento y tengo mucho lag": "diagnostico_latencia",
            "no tengo internet": "diagnostico_conectividad",
            "Quiero revisar mi red": "diagnostico_general",
            "¿Qué canal wifi me conviene?": "analizar_wifi",
            "dame información de mi router": "info_router",
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(intencion(texto), esperado)

    def test_listar_dispositivos(self):
        for texto in ["¿Cuántos usuarios hay en mi red?", "dispositivos conectados al wifi",
                      "quién está usando mi wifi", "cuantas personas estan conectadas",
                      "hay alguien robandome el internet"]:
            with self.subTest(texto=texto):
                self.assertEqual(intencion(texto), "listar_dispositivos")

    def test_sin_acentos_ni_mayusculas(self):
        self.assertEqual(intencion("SIN CONEXION"), "diagnostico_conectividad")
        self.assertEqual(intencion("sin conexión"), "diagnostico_conectividad")

    def test_palabra_completa(self):
        # 'lag' no debe coincidir dentro de 'plaga'.
        self.assertEqual(intencion("hay una plaga de mosquitos"), "intencion_desconocida")

    def test_entradas_vacias_o_raras(self):
        for t in ["", "   ", "\x00\x01", None, 123]:
            with self.subTest(t=t):
                self.assertEqual(intencion(t), "intencion_desconocida")

    def test_clasificador_generaliza_frases_nuevas(self):
        self.assertEqual(intencion("mi pelicula se traba y no avanza"), "diagnostico_latencia")


if __name__ == "__main__":
    unittest.main()
