import unittest

from src.discovery import (parsear_gateway_linux, parsear_gateway_macos,
                           parsear_gateway_windows, parsear_proc_net_route)

ROUTE_PRINT = """IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0      192.168.100.1   192.168.100.35     25
          0.0.0.0          0.0.0.0      10.0.0.1        10.0.0.7           50
        127.0.0.0        255.0.0.0         On-link         127.0.0.1    331
"""


class TestGateway(unittest.TestCase):
    def test_windows_elige_menor_metrica(self):
        self.assertEqual(parsear_gateway_windows(ROUTE_PRINT), "192.168.100.1")

    def test_windows_on_link_se_ignora(self):
        texto = "          0.0.0.0          0.0.0.0         On-link   10.0.0.7   25"
        self.assertIsNone(parsear_gateway_windows(texto))

    def test_linux_ip_route(self):
        self.assertEqual(
            parsear_gateway_linux("default via 192.168.1.254 dev wlan0 proto dhcp"),
            "192.168.1.254")

    def test_macos(self):
        self.assertEqual(
            parsear_gateway_macos("   route to: default\n    gateway: 192.168.0.1\n"),
            "192.168.0.1")

    def test_proc_net_route_hex_invertido(self):
        texto = ("Iface\tDestination\tGateway\n"
                 "eth0\t00000000\t0101A8C0\t0003\n")
        self.assertEqual(parsear_proc_net_route(texto), "192.168.1.1")

    def test_sin_gateway(self):
        self.assertIsNone(parsear_gateway_linux(""))
        self.assertIsNone(parsear_gateway_windows(""))


if __name__ == "__main__":
    unittest.main()
