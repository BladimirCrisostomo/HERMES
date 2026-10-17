import unittest

from src.router.wifi_analyzer import (WiFiAnalyzer, interferencia,
                                      parsear_canales_nmcli, parsear_canales_windows)

NETSH = """SSID 1 : RedA
    BSSID 1  : aa:bb
         Señal: 80%
         Canal                  : 6
SSID 2 : RedB
    BSSID 1  : cc:dd
         Channel                : 11
"""


class TestWifi(unittest.TestCase):
    def test_parseo_windows_es_y_en(self):
        self.assertEqual(parsear_canales_windows(NETSH), [6, 11])

    def test_parseo_nmcli(self):
        self.assertEqual(parsear_canales_nmcli("6\n11\n149\n\n"), [6, 11, 149])

    def test_interferencia_por_solapamiento(self):
        # Una red en el canal 3 afecta al 1 y al 6, pero más al 1 (más cercano)... y menos al 11.
        self.assertGreater(interferencia([3], 1), 0)
        self.assertGreater(interferencia([3], 6), 0)
        self.assertEqual(interferencia([3], 11), 0)

    def test_recomienda_canal_menos_afectado(self):
        datos = {"correcto": True, "canales_detectados": [1, 1, 1, 2, 6, 6, 5]}
        informe = WiFiAnalyzer().analizar(datos)
        self.assertEqual(informe["canal_recomendado"], 11)

    def test_redes_5ghz_no_cuentan_para_24ghz(self):
        informe = WiFiAnalyzer().analizar({"correcto": True, "canales_detectados": [36, 40, 6]})
        self.assertEqual(informe["redes_5ghz_ignoradas"], 2)

    def test_errores(self):
        self.assertFalse(WiFiAnalyzer().analizar({"correcto": False, "error": "x"})["correcto"])
        self.assertFalse(WiFiAnalyzer().analizar({"correcto": True, "canales_detectados": []})["correcto"])


if __name__ == "__main__":
    unittest.main()
