import unittest

from src.seguridad import (es_ip_privada, exigir_ip_privada, sanitizar_texto,
                           validar_host, validar_mac)


class TestSeguridad(unittest.TestCase):
    def test_host_valido(self):
        self.assertEqual(validar_host("8.8.8.8"), "8.8.8.8")
        self.assertEqual(validar_host("google.com"), "google.com")

    def test_host_con_opciones_o_comandos_se_rechaza(self):
        for malo in ["-f", "--help", "8.8.8.8; rm -rf /", "a b", "", "$(whoami)", None]:
            with self.subTest(host=malo):
                with self.assertRaises(ValueError):
                    validar_host(malo)

    def test_ip_privada(self):
        self.assertTrue(es_ip_privada("192.168.1.1"))
        self.assertTrue(es_ip_privada("10.0.0.5"))
        self.assertFalse(es_ip_privada("8.8.8.8"))
        self.assertFalse(es_ip_privada("no es ip"))
        with self.assertRaises(ValueError):
            exigir_ip_privada("1.1.1.1")

    def test_mac(self):
        self.assertEqual(validar_mac("aa-bb-cc-dd-ee-ff"), "AA:BB:CC:DD:EE:FF")
        with self.assertRaises(ValueError):
            validar_mac("192.168.1.35")

    def test_sanitizar_texto(self):
        self.assertEqual(sanitizar_texto("hola\x00\x1b mundo"), "hola mundo")
        self.assertEqual(len(sanitizar_texto("a" * 1000, 300)), 300)
        self.assertEqual(sanitizar_texto(None), "")


if __name__ == "__main__":
    unittest.main()
