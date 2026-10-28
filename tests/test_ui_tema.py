import unittest

from src import ui_tema as ui


class TestTema(unittest.TestCase):
    def test_los_nombres_de_dispositivos_se_escapan(self):
        malo = '<script>alert("x")</script><img src=x onerror=alert(1)>'
        html = ui.tabla_dispositivos([{"ip": "1.1.1.1", "mac": "AA:BB:CC:00:00:01", "nombre": malo}])
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;", html)

    def test_cualquier_texto_dinamico_se_escapa(self):
        self.assertNotIn("<b>", ui.panel("<b>t</b>", "<p>ok</p>").split("hud-t")[1].split("</div>")[0])
        self.assertNotIn("<i>", ui.chip("<i>x</i>"))
        self.assertNotIn("<u>", ui.banner("<u>x</u>"))
        self.assertNotIn("<s>", ui.hero("conectado", "<s>x</s>"))
        self.assertNotIn("<e>", ui.medidor("<e>", 5, "ms", "ok", 10))

    def test_niveles(self):
        self.assertEqual([ui.nivel_latencia(x) for x in (None, 20, 70, 200)], ["off", "ok", "warn", "bad"])
        self.assertEqual([ui.nivel_perdida(x) for x in (0, 5, 20)], ["ok", "warn", "bad"])
        self.assertEqual([ui.nivel_jitter(x) for x in (3, 20, 50)], ["ok", "warn", "bad"])
        self.assertEqual(ui.nivel_de_problema("estable"), "ok")
        self.assertEqual(ui.nivel_de_problema("latencia_alta"), "bad")

    def test_medidor_sin_dato_y_con_cero(self):
        self.assertIn("—", ui.medidor("L", None, "ms", "off", 100))
        self.assertIn("--p:0", ui.medidor("P", 0, "%", "ok", 30))
        self.assertIn("--p:100", ui.medidor("L", 999, "ms", "bad", 200))

    def test_el_estado_del_heroe_cambia_la_clase(self):
        for estado in ui.ESTADOS:
            self.assertIn(f"estado-{estado}", ui.hero(estado))

    def test_etiquetas_de_la_tabla(self):
        html = ui.tabla_dispositivos([{"ip": "a", "mac": "m", "bloqueado": True, "mac_aleatoria": True}])
        self.assertIn("bloqueado", html)
        self.assertIn("MAC privada", html)


if __name__ == "__main__":
    unittest.main()
