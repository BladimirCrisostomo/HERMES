import io
import logging
import os
import unittest
from unittest import mock

from src import credenciales
from src.credenciales import (Credenciales, advertencia_transporte, desde_entorno,
                              pedir_credenciales)
from src.seguridad import FiltroSecretos


class TestCredenciales(unittest.TestCase):
    def test_la_contrasena_no_aparece_al_imprimir(self):
        c = Credenciales("admin", "SuperSecreta123")
        self.assertNotIn("SuperSecreta123", repr(c))
        self.assertNotIn("SuperSecreta123", str(c))

    def test_los_logs_ocultan_la_contrasena(self):
        Credenciales("admin", "ClaveDePrueba987")
        flujo = io.StringIO()
        manejador = logging.StreamHandler(flujo)
        manejador.addFilter(FiltroSecretos())
        log = logging.getLogger("prueba.secretos")
        log.propagate = False
        log.addHandler(manejador)
        log.warning("Intentando iniciar sesión con ClaveDePrueba987 en el router")
        self.assertNotIn("ClaveDePrueba987", flujo.getvalue())
        self.assertIn("***", flujo.getvalue())

    def test_pedir_credenciales_con_valores_por_defecto(self):
        c = pedir_credenciales("192.168.1.1", entrada=lambda _: "", clave=lambda _: "pw12345")
        self.assertEqual((c.usuario, c.contrasena), ("admin", "pw12345"))

    def test_solo_contrasena_no_pregunta_el_usuario(self):
        def no_debe_llamarse(_):
            raise AssertionError("no debía pedir el usuario")
        c = pedir_credenciales("192.168.1.1", entrada=no_debe_llamarse, clave=lambda _: "pw12345",
                               pedir_usuario=False)
        self.assertEqual((c.usuario, c.contrasena), ("admin", "pw12345"))

    def test_contrasena_vacia_se_rechaza(self):
        with self.assertRaises(ValueError):
            pedir_credenciales("192.168.1.1", entrada=lambda _: "x", clave=lambda _: "")

    def test_solo_pide_credenciales_para_ips_privadas(self):
        with self.assertRaises(ValueError):
            pedir_credenciales("8.8.8.8", entrada=lambda _: "x", clave=lambda _: "y")

    def test_desde_entorno(self):
        with mock.patch.dict(os.environ, {"HERMES_ROUTER_USER": "u", "HERMES_ROUTER_PASS": "pass123"}):
            self.assertEqual(desde_entorno().usuario, "u")
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(desde_entorno())

    def test_llavero_opcional(self):
        with mock.patch.object(credenciales, "_llavero", return_value=None):
            self.assertFalse(credenciales.guardar_en_llavero("192.168.1.1", Credenciales("a", "bcd")))
            self.assertIsNone(credenciales.cargar_de_llavero("192.168.1.1"))

    def test_advertencia_http(self):
        self.assertIsNotNone(advertencia_transporte({"http": True, "https": False}))
        self.assertIsNone(advertencia_transporte({"http": True, "https": True}))


if __name__ == "__main__":
    unittest.main()
