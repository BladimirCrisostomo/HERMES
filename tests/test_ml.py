import unittest

from scripts.generar_dataset import CLASES, generar
from src.machine_learning import CARACTERISTICAS, entrenar_modelo, predecir_problema


class TestML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = generar(por_clase=150, semilla=7)
        cls.modelo, cls.metricas = entrenar_modelo(cls.datos)

    def test_dataset_equilibrado_y_completo(self):
        self.assertEqual(set(self.datos["problema"]), set(CLASES))
        self.assertEqual(self.datos["problema"].value_counts().nunique(), 1)
        self.assertFalse(self.datos[CARACTERISTICAS].isna().any().any())

    def test_accuracy_razonable(self):
        self.assertGreater(self.metricas["accuracy_cv_media"], 0.85)
        self.assertGreater(self.metricas["accuracy_prueba"], 0.85)

    def test_entrenamiento_reproducible(self):
        _, otras = entrenar_modelo(self.datos)
        self.assertEqual(otras["accuracy_prueba"], self.metricas["accuracy_prueba"])

    def test_prediccion_devuelve_etiqueta_y_confianza(self):
        c = dict(latencia=25, perdida=0, jitter=3, latencia_gateway=2, perdida_gateway=0)
        etiqueta, confianza = predecir_problema(self.modelo, c)
        self.assertEqual(etiqueta, "estable")
        self.assertTrue(0 < confianza <= 1)


if __name__ == "__main__":
    unittest.main()
