import ipaddress
import unittest

from src.dispositivos import (construir_dispositivos, es_mac_aleatoria, fabricante_de,
                              macs_protegidas, normalizar_mac, parsear_tabla_arp)

RED = ipaddress.ip_network("192.168.100.0/24")
ARP_WINDOWS = """
Interface: 192.168.100.35 --- 0x5
  Internet Address      Physical Address      Type
  192.168.100.1         b8-27-eb-11-22-33     dynamic
  192.168.100.20        da-a1-19-00-00-02     dynamic
  192.168.100.255       ff-ff-ff-ff-ff-ff     static
  224.0.0.22            01-00-5e-00-00-16     static
  239.255.255.250       01-00-5e-7f-ff-fa     static
  10.9.9.9              aa-aa-aa-aa-aa-aa     dynamic
"""
ARP_LINUX = """192.168.100.1 dev wlan0 lladdr b8:27:eb:11:22:33 REACHABLE
192.168.100.30 dev wlan0  FAILED
fe80::1 dev wlan0 lladdr aa:bb:cc:dd:ee:ff router STALE
"""
ARP_MACOS = "? (192.168.100.5) at a:b:c:d:e:f on en0 ifscope [ethernet]"


class TestParseoARP(unittest.TestCase):
    def test_windows_filtra_broadcast_multicast_y_otras_redes(self):
        tabla = parsear_tabla_arp(ARP_WINDOWS, RED)
        self.assertEqual(set(tabla), {"192.168.100.1", "192.168.100.20"})

    def test_linux_ignora_incompletas_e_ipv6(self):
        self.assertEqual(parsear_tabla_arp(ARP_LINUX, RED), {"192.168.100.1": "B8:27:EB:11:22:33"})

    def test_macos_completa_ceros(self):
        self.assertEqual(parsear_tabla_arp(ARP_MACOS, RED), {"192.168.100.5": "0A:0B:0C:0D:0E:0F"})

    def test_normalizar_mac(self):
        self.assertEqual(normalizar_mac("a-b-c-d-e-f"), "0A:0B:0C:0D:0E:0F")


class TestDispositivos(unittest.TestCase):
    def test_mac_aleatoria_y_fabricante(self):
        self.assertTrue(es_mac_aleatoria("DA:A1:19:00:00:02"))     # bit local activado
        self.assertFalse(es_mac_aleatoria("B8:27:EB:11:22:33"))
        self.assertEqual(fabricante_de("B8:27:EB:11:22:33"), "Raspberry Pi")
        self.assertIsNone(fabricante_de("DA:A1:19:00:00:02"))      # aleatoria: no se adivina
        self.assertIsNone(fabricante_de(None))

    def test_construccion_y_orden(self):
        tabla = parsear_tabla_arp(ARP_WINDOWS, RED)
        lista = construir_dispositivos(tabla, "192.168.100.35", "192.168.100.1",
                                       {"192.168.100.20": "movil"}, "AA:00:00:00:00:35")
        self.assertEqual([d.ip for d in lista], ["192.168.100.1", "192.168.100.20", "192.168.100.35"])
        self.assertTrue(lista[0].es_gateway)
        self.assertTrue(lista[2].es_este_equipo)
        self.assertEqual(lista[1].nombre, "movil")
        self.assertTrue(lista[1].mac_aleatoria)

    def test_este_equipo_aparece_aunque_no_se_conozca_su_mac(self):
        lista = construir_dispositivos({}, "192.168.100.35", None)
        self.assertEqual(len(lista), 1)
        self.assertTrue(lista[0].es_este_equipo)

    def test_macs_protegidas_son_este_equipo_y_router(self):
        tabla = parsear_tabla_arp(ARP_WINDOWS, RED)
        lista = construir_dispositivos(tabla, "192.168.100.35", "192.168.100.1", None, "AA:00:00:00:00:35")
        self.assertEqual(macs_protegidas(lista), {"B8:27:EB:11:22:33", "AA:00:00:00:00:35"})


if __name__ == "__main__":
    unittest.main()
