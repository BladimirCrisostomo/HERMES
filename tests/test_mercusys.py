"""Pruebas del adaptador MW306R con un router SIMULADO que habla el mismo protocolo.

Todos los datos son inventados (MAC AA-BB-CC-..., clave falsa); no provienen de ningún router real.
"""
import io
import logging
import re
import unittest

from src.politicas import GuardianRouter, Modo
from src.router import registro
from src.router.adapters import mercusys_mw306r as mw
from src.router.manager import RouterManager
from src.seguridad import FiltroSecretos

import string

from src.credenciales import Credenciales

CLAVE_LOGIN = "abcdefghijklmnopqrstuvwxyz012345"            # authInfo[3] inventado (32 car.)
TABLA = ("".join(chr(c) for c in range(33, 127)) * 3)[:255]  # tabla inventada de 255 caracteres
PASSWORD = "PasswordDePrueba7"
CERO = "00-00-00-00-00-00"


class RouterFalso:
    """Imita el panel: login por id cifrado y respuestas 'code=N&asyn=M&id=...'."""

    def __init__(self, password=PASSWORD, modelo="MW306R"):
        self.canal = 0
        self.acceso_activo, self.lista_blanca = True, False
        self.lista_negra = []
        self.rechazar_escrituras = False
        self.ignorar_bloqueos = False
        self.comandos = []
        self.sin_linea_de_codigo = False
        self.sondas = []            # códigos de las peticiones sin id (parámetros de login)
        self.intentos_login = 0
        self.modelo = modelo
        self.id_valido = mw.codificar_para_url(mw.cifrar(CLAVE_LOGIN, password, TABLA))

    def _objeto(self, oid):
        if oid == "0|1,0,0":
            return f"modelName {self.modelo}\r\nfacturer MERCUSYS\r\nsoftVer 1.4.4%20Build\r\n"
        if oid == "13|1,0,0":
            return ("ip 0 192.168.1.101\r\nip 1 192.168.1.102\r\nip 2 192.168.1.103\r\nip 3 192.168.1.104\r\n"
                    "ip 4 0.0.0.0\r\nmac 0 AA-BB-CC-00-00-01\r\nmac 1 AA-BB-CC-00-00-02\r\n"
                    f"mac 2 AA-BB-CC-00-00-03\r\nmac 3 AA-BB-CC-00-00-04\r\nmac 4 {CERO}\r\n")
        if oid == "9|1,0,0":
            return ("hostName 0 laptop\r\nhostName 1 telefono\r\nhostName 2 tv\r\nhostName 3 consola\r\n"
                    "hostName 4 \r\nmac 0 AA-BB-CC-00-00-01\r\nmac 1 AA-BB-CC-00-00-02\r\n"
                    f"mac 2 AA-BB-CC-00-00-03\r\nmac 3 AA-BB-CC-00-00-04\r\nmac 4 {CERO}\r\n")
        if oid == "73|1,0,0":
            filas = "".join(f"devName {i} {n}\r\nmac {i} {m}\r\n" for i, (n, m) in enumerate(self.lista_negra))
            return filas or f"devName 0 \r\nmac 0 {CERO}\r\n"
        if oid == "58|1,0,0":
            return f"ctrlEnable {int(self.acceso_activo)}\r\nisWhiteList {int(self.lista_blanca)}\r\n"
        if oid == "32|1,0,0":
            return f"uBand 0\r\nbEnabled 1\r\nuChannel {self.canal}\r\nuBgnMode 5\r\n"
        if oid == "33|1,1,0":
            return ("uUnit 0\r\nuPskGKUpdateIntvl 0\r\nuKeyLength 0 0\r\nuKeyLength 1 0\r\n"
                    "cKeyVal 0 \r\ncKeyVal 1 \r\ncSsid RedDePrueba\r\ncPskSecret ClaveFalsaDePrueba99\r\n")
        if oid == "1|1,0,0":
            return "authKey LlaveFalsa123\r\nmac 0 AA-BB-CC-00-00-FF\r\nmac 1 AA-BB-CC-00-00-FE\r\n"
        if oid == "4|1,0,0":
            return "ip 192.168.1.1\r\nmask 255.255.255.0\r\n"
        return ""

    def transporte(self, ruta, cuerpo):
        m = re.match(r"/\?code=(\d)&asyn=(\d)(?:&id=(.*))?$", ruta)
        code, sesion = m.group(1), m.group(3)
        if code in ("2", "7") and sesion is None:  # parámetros de login: 401 sin credenciales
            self.sondas.append(code)
            if self.sin_linea_de_codigo:   # estructura antigua hipotética: sin código al inicio
                return 401, f"aaaaa\r\nbbbbb\r\n{CLAVE_LOGIN}\r\n{TABLA}\r\n"
            # Estructura REAL observada en un MW306R: largos [5, 5, 5, 32, 255, 5]
            return 401, f"00007\r\naaaaa\r\nbbbbb\r\n{CLAVE_LOGIN}\r\n{TABLA}\r\nccccc\r\n"
        if code == "7":
            self.intentos_login += 1
        if sesion != self.id_valido:
            return 401, ""
        if code == "7":
            return 200, ""
        if code == "2":
            return 200, "00000\r\n" + "".join(f"id {o}\r\n{self._objeto(o)}" for o in cuerpo.split("#"))
        if code == "1":
            if self.rechazar_escrituras:
                return 200, "00001\r\n"
            for linea in cuerpo.split("\r\n"):
                if linea.startswith("uChannel "):
                    self.canal = int(linea.split()[1])
            return 200, "00000\r\n"
        self.comandos.append(cuerpo)
        if cuerpo == "wlan channelList 2g":
            return 200, "00000\r\n0 1 2 3 4 5 6 7 8 9 10 11"
        if cuerpo.startswith("advanced bm -add list:black") and not self.ignorar_bloqueos:
            nombre = re.search(r"name:(\S+)", cuerpo).group(1)
            self.lista_negra.append((nombre, re.search(r"mac:(\S+)", cuerpo).group(1)))
        if cuerpo.startswith("advanced bm rule -del list:black"):
            mac = re.search(r"mac:(\S+)", cuerpo).group(1)
            self.lista_negra = [(n, x) for n, x in self.lista_negra if x != mac]
        return 200, "00000\r\n"


def adaptador(router=None, conectar=True):
    router = router or RouterFalso()
    a = mw.MercusysMW306R("192.168.1.1", Credenciales("admin", PASSWORD), transporte=router.transporte)
    if conectar:
        a.conectar()
    return a, router


class TestParseo(unittest.TestCase):
    def test_codigo_de_error(self):
        with self.assertRaises(mw.ErrorRouter):
            mw.parsear_respuesta("00001\r\n")

    def test_clientes_unidos_y_sin_filas_vacias(self):
        a, router = adaptador()
        router.lista_negra = [("telefono", "AA-BB-CC-00-00-02")]
        clientes = a.obtener_clientes()
        self.assertEqual([c["mac"] for c in clientes],
                         ["AA:BB:CC:00:00:0%d" % n for n in (1, 2, 3, 4)])
        self.assertEqual(clientes[0]["nombre"], "laptop")
        self.assertEqual(clientes[0]["ip"], "192.168.1.101")
        self.assertFalse(clientes[0]["bloqueado"])
        self.assertTrue(clientes[1]["bloqueado"])

    def test_canales(self):
        self.assertEqual(mw.parsear_canales("00000\r\n0 1 2 3 11"), [1, 2, 3, 11])

    def test_informacion_del_router(self):
        a, _ = adaptador()
        info = a.obtener_informacion()
        self.assertEqual((info["modelo"], info["ip_lan"], info["mac_router"]),
                         ("MW306R", "192.168.1.1", "AA:BB:CC:00:00:FF"))

    def test_serializar_intercala_claves_wep_y_aplica_cambios(self):
        obj = mw.parsear_respuesta("00000\r\nid 33|1,1,0\r\n" + RouterFalso()._objeto("33|1,1,0"))["33|1,1,0"]
        texto = mw.serializar_objeto("33|1,1,0", obj, {"cSsid": "Otra"})
        self.assertIn("uPskGKUpdateIntvl 0\r\nuKeyLength 0 0\r\ncKeyVal 0 \r\nuKeyLength 1 0\r\ncKeyVal 1 \r\n", texto)
        self.assertIn("cSsid Otra", texto)
        self.assertTrue(texto.startswith("id 33|1,1,0\r\n"))


class TestAcciones(unittest.TestCase):
    def test_cambiar_canal_escribe_y_verifica(self):
        a, router = adaptador()
        a.cambiar_canal(3)
        self.assertEqual(router.canal, 3)
        self.assertEqual(a.obtener_configuracion_wifi()["canal"], 3)

    def test_canal_fuera_de_region_se_rechaza_sin_escribir(self):
        a, router = adaptador()
        with self.assertRaises(ValueError):
            a.cambiar_canal(12)           # la región del router solo permite 1-11
        self.assertEqual(router.canal, 0)

    def test_canal_cero_es_automatico(self):
        a, router = adaptador()
        a.cambiar_canal(6)
        a.cambiar_canal(0)
        self.assertEqual(router.canal, 0)

    def test_router_que_rechaza_la_escritura(self):
        a, router = adaptador()
        router.rechazar_escrituras = True
        with self.assertRaises(mw.ErrorRouter):
            a.cambiar_canal(3)

    def test_la_escritura_conserva_la_clave_wifi_sin_filtrarla_a_los_logs(self):
        a, router = adaptador()
        enviados = []
        original = router.transporte
        a._transporte = lambda ruta, cuerpo: (enviados.append(cuerpo), original(ruta, cuerpo))[1]
        a.cambiar_canal(3)
        escritura = next(c for c in enviados if c.startswith("id 32"))
        self.assertIn("cPskSecret ClaveFalsaDePrueba99", escritura)     # se reenvía intacta
        flujo = io.StringIO()
        h = logging.StreamHandler(flujo)
        h.addFilter(FiltroSecretos())
        log = logging.getLogger("prueba.mw306r")
        log.propagate = False
        log.addHandler(h)
        log.warning("cuerpo enviado: %s", escritura)
        self.assertNotIn("ClaveFalsaDePrueba99", flujo.getvalue())

    def test_bloqueo_arma_el_comando_exacto(self):
        a, router = adaptador()
        a.bloquear_cliente("AA:BB:CC:00:00:02")
        self.assertEqual(router.comandos[-1], "advanced bm -add list:black name:telefono mac:AA-BB-CC-00-00-02")

    def test_bloqueo_no_activa_el_control_de_acceso_por_su_cuenta(self):
        a, router = adaptador()
        router.acceso_activo = False
        with self.assertRaises(mw.ErrorRouter):
            a.bloquear_cliente("AA:BB:CC:00:00:02")
        self.assertEqual(router.lista_negra, [])

    def test_comando_bloquear_sanea_el_nombre(self):
        c = mw.comando_bloquear("aa:bb:cc:00:00:02", "mi tel; reboot")
        self.assertEqual(c, "advanced bm -add list:black name:mi_tel__reboot mac:AA-BB-CC-00-00-02")
        with self.assertRaises(ValueError):
            mw.comando_bloquear("no-es-mac", "x")

    def test_sin_sesion(self):
        a, _ = adaptador(conectar=False)
        with self.assertRaises(mw.ErrorRouter):
            a.obtener_clientes()

    def test_desbloqueo_arma_el_comando_exacto_y_verifica(self):
        a, router = adaptador()
        a.bloquear_cliente("AA:BB:CC:00:00:02")
        a.desbloquear_cliente("AA:BB:CC:00:00:02")
        self.assertEqual(router.comandos[-1], "advanced bm rule -del list:black mac:AA-BB-CC-00-00-02")
        self.assertEqual(router.lista_negra, [])

    def test_bloqueo_que_el_router_ignora_se_detecta(self):
        a, router = adaptador()
        router.ignorar_bloqueos = True
        with self.assertRaises(mw.ErrorRouter):
            a.bloquear_cliente("AA:BB:CC:00:00:02")

    def test_qos_y_reinicio_siguen_pendientes(self):
        a, _ = adaptador()
        for accion in (lambda: a.limitar_cliente("AA:BB:CC:00:00:02", 1000),
                       lambda: a.quitar_limite("AA:BB:CC:00:00:02"), a.reiniciar):
            with self.assertRaises(NotImplementedError):
                accion()


class TestLogin(unittest.TestCase):
    def test_los_pasos_del_login_se_registran_sin_secretos(self):
        a, router = adaptador()
        pasos = a.pasos_login
        self.assertEqual(pasos["1_parametros"]["http"], 401)
        self.assertEqual(pasos["2_login"]["http"], 200)
        self.assertEqual(pasos["3_lectura"]["modelo"], "MW306R")
        for secreto in (PASSWORD, CLAVE_LOGIN, router.id_valido):
            self.assertNotIn(secreto, str(pasos))

    def test_los_parametros_se_toman_de_las_lineas_de_32_y_255_no_de_las_de_5(self):
        a, router = adaptador()
        pasos = a.pasos_login["1_parametros"]
        self.assertEqual(pasos["largos"], [5, 5, 5, 32, 255, 5])      # misma estructura que el router real
        self.assertEqual(pasos["indice_tabla"], 4)
        self.assertIsNotNone(a._sesion)                              # el login funcionó con esos parámetros

    def test_tambien_funciona_si_el_router_no_envia_linea_de_codigo(self):
        router = RouterFalso()
        router.sin_linea_de_codigo = True
        a, _ = adaptador(router)
        self.assertEqual(a.pasos_login["1_parametros"]["indice_tabla"], 3)
        self.assertIsNotNone(a._sesion)

    def test_parametros_de_formato_inesperado_se_rechazan(self):
        for cuerpo in ["a\r\nb\r\nc\r\nd\r\n", "00007\r\n\r\n" + "t" * 40 + "\r\n"]:
            with self.subTest(cuerpo=cuerpo[:12]):
                a = mw.MercusysMW306R("192.168.1.1", Credenciales("admin", PASSWORD),
                                      transporte=lambda r, c, x=cuerpo: (401, x))
                with self.assertRaises(mw.ErrorRouter):
                    a.conectar()

    def test_pide_los_parametros_con_code_2_justo_antes_de_iniciar_sesion(self):
        _, router = adaptador()
        self.assertEqual(router.sondas[-1], "2")      # como hace el panel (getLoginParams)

    def test_un_login_fallido_hace_un_solo_intento_y_deja_el_diagnostico(self):
        router = RouterFalso(password="otra-distinta")
        a, _ = adaptador(router, conectar=False)
        with self.assertRaises(mw.ErrorRouter):
            a.conectar()
        self.assertEqual(router.intentos_login, 1)      # no se reintenta para "diagnosticar"
        self.assertEqual(a.pasos_login["2_login"]["http"], 401)

    def test_cifrado_coincide_con_calculos_a_mano(self):
        self.assertEqual(mw.cifrar("ab", "cd", "0123456789"), "26")
        self.assertEqual(mw.cifrar("a", "cd", "0123456789"), "23")     # t más corto que la clave
        self.assertEqual(mw.cifrar("abc", "c", "0123456789"), "276")   # clave más corta que t

    def test_codificacion_como_encodeuricomponent(self):
        self.assertEqual(mw.codificar_para_url("Ab12!Xy<Zq{Wv"), "Ab12!Xy%3CZq%7BWv")
        self.assertEqual(mw.codificar_para_url("a^b|c+d"), "a%5Eb%7Cc%2Bd")

    def test_login_correcto_verifica_el_modelo(self):
        a, _ = adaptador()
        self.assertIsNotNone(a._sesion)
        self.assertEqual(a.obtener_informacion()["modelo"], "MW306R")

    def test_la_sesion_no_aparece_en_los_logs(self):
        a, router = adaptador()
        flujo = io.StringIO()
        h = logging.StreamHandler(flujo)
        h.addFilter(FiltroSecretos())
        log = logging.getLogger("prueba.login")
        log.propagate = False
        log.addHandler(h)
        log.warning("GET /?code=2&asyn=1&id=%s", a._sesion)
        self.assertNotIn(a._sesion, flujo.getvalue())

    def test_contrasena_incorrecta(self):
        router = RouterFalso(password="OtraClaveDistinta")
        a, _ = adaptador(router, conectar=False)
        with self.assertRaises(mw.ErrorRouter):
            a.conectar()
        self.assertIsNone(a._sesion)

    def test_otro_modelo_se_rechaza(self):
        router = RouterFalso(modelo="MR50G")
        a, _ = adaptador(router, conectar=False)
        with self.assertRaises(mw.ErrorRouter) as ctx:
            a.conectar()
        self.assertIn("MW306R", str(ctx.exception))
        self.assertIsNone(a._sesion)

    def test_respuesta_inesperada_al_pedir_parametros(self):
        a = mw.MercusysMW306R("192.168.1.1", Credenciales("admin", PASSWORD),
                              transporte=lambda r, c: (200, "hola"))
        with self.assertRaises(mw.ErrorRouter):
            a.conectar()

    def test_sin_credenciales_o_contrasena_demasiado_larga(self):
        with self.assertRaises(mw.ErrorRouter):
            mw.MercusysMW306R("192.168.1.1", None, transporte=RouterFalso().transporte).conectar()
        with self.assertRaises(mw.ErrorRouter):
            mw.MercusysMW306R("192.168.1.1", Credenciales("admin", "x" * 33),
                              transporte=RouterFalso().transporte).conectar()


class TestConElGuardian(unittest.TestCase):
    class RedCaida:
        def antes(self): pass
        def despues(self): return False

    class RedSana(RedCaida):
        def despues(self): return True

    def _guardian(self, verificador):
        a, router = adaptador()
        m = RouterManager()
        m.establecer_router(a)
        return GuardianRouter(m, Modo.AUTOMATICO, verificador=verificador,
                              espera_verificacion=0, dormir=lambda s: None), router

    def test_cambio_de_canal_automatico_y_verificado(self):
        g, router = self._guardian(self.RedSana())
        self.assertTrue(g.ejecutar("cambiar_canal", 6).ejecutada)
        self.assertEqual(router.canal, 6)

    def test_si_la_red_cae_vuelve_al_canal_automatico_original(self):
        g, router = self._guardian(self.RedCaida())
        r = g.ejecutar("cambiar_canal", 6)
        self.assertTrue(r.revertida)
        self.assertEqual(router.canal, 0)

    def test_bloqueo_con_confirmacion(self):
        g, router = self._guardian(self.RedSana())
        r = g.ejecutar("bloquear_cliente", "AA:BB:CC:00:00:02", lambda t: True)
        self.assertTrue(r.ejecutada)
        self.assertEqual(len(router.lista_negra), 1)

    def test_bloqueo_sin_confirmacion_no_se_hace_ni_en_automatico(self):
        g, router = self._guardian(self.RedSana())
        self.assertFalse(g.ejecutar("bloquear_cliente", "AA:BB:CC:00:00:02").ejecutada)
        self.assertEqual(router.lista_negra, [])

    def test_si_la_red_cae_tras_bloquear_se_desbloquea(self):
        g, router = self._guardian(self.RedCaida())
        r = g.ejecutar("bloquear_cliente", "AA:BB:CC:00:00:02", lambda t: True)
        self.assertTrue(r.revertida)
        self.assertEqual(router.lista_negra, [])

    def test_limitar_y_reiniciar_no_estan_habilitados_todavia(self):
        g, _ = self._guardian(self.RedSana())
        self.assertFalse(g.ejecutar("limitar_cliente", ("AA:BB:CC:00:00:02", 1000)).ejecutada)
        self.assertFalse(g.ejecutar("reiniciar", None, lambda t: True).ejecutada)


class TestHuellaYBusqueda(unittest.TestCase):
    def test_el_protocolo_del_panel_se_reconoce_sin_depender_del_html(self):
        router = RouterFalso()
        self.assertTrue(mw.responde_al_protocolo("192.168.1.1", router.transporte))

    def test_un_modem_cualquiera_no_se_confunde(self):
        for respuesta in [(404, "no existe"), (200, "<html>módem</html>"), (401, "una sola linea")]:
            with self.subTest(respuesta=respuesta):
                self.assertFalse(mw.responde_al_protocolo("192.168.100.1", lambda r, c, x=respuesta: x))

    def test_sin_respuesta_de_red(self):
        def caido(ruta, cuerpo):
            raise OSError("sin ruta")
        self.assertFalse(mw.responde_al_protocolo("192.168.1.1", caido))

    def test_la_huella_del_protocolo_basta_para_elegir_el_adaptador(self):
        info, puntaje = registro.elegir_adaptador({"fabricante": None, "titulo": None, "protocolo_panel": True})
        self.assertEqual((info.nombre, puntaje), ("mercusys_mw306r", 70))

    def test_buscar_routers_distingue_compatibles(self):
        huellas = {"192.168.1.1": {"protocolo_panel": True, "titulo": "Mercusys", "servidor": "Boa"},
                   "192.168.100.1": {"protocolo_panel": False, "titulo": "Modem", "servidor": "ISP"}}
        originales = (registro.obtener_huella, registro.RouterDetector.comprobar_puerto)
        registro.obtener_huella = lambda ip: huellas[ip]
        registro.RouterDetector.comprobar_puerto = lambda self, puerto, timeout=1: self.ip in huellas
        try:
            r = {h["ip"]: h for h in registro.buscar_routers()}
        finally:
            registro.obtener_huella, registro.RouterDetector.comprobar_puerto = originales
        self.assertEqual(set(r), {"192.168.1.1", "192.168.100.1"})
        self.assertEqual(r["192.168.1.1"]["adaptador"], "mercusys_mw306r")
        self.assertIsNone(r["192.168.100.1"]["adaptador"])

    def test_buscar_routers_ignora_ips_publicas(self):
        originales = (registro.obtener_huella, registro.RouterDetector.comprobar_puerto)
        registro.RouterDetector.comprobar_puerto = lambda self, puerto, timeout=1: False
        try:
            self.assertEqual(registro.buscar_routers(extra=["8.8.8.8"]), [])
        finally:
            registro.obtener_huella, registro.RouterDetector.comprobar_puerto = originales


class TestRegistro(unittest.TestCase):
    def test_se_elige_para_routers_mercusys(self):
        info, puntaje = registro.elegir_adaptador({"fabricante": "MERCUSYS", "titulo": "x"})
        self.assertEqual(info.nombre, "mercusys_mw306r")
        self.assertGreater(puntaje, 0)

    def test_no_se_elige_para_otras_marcas(self):
        self.assertEqual(registro.elegir_adaptador({"fabricante": "NETGEAR"}), (None, 0))

    def test_conectar_maneja_un_router_que_no_responde(self):
        class Caido:
            def __init__(self, ip, cred): pass
            def conectar(self): raise OSError("sin respuesta")
        original_huella, original_clase = registro.obtener_huella, registro.MercusysMW306R
        registro.obtener_huella = lambda ip: {"ip": ip, "servicios": {"http": True, "https": False},
                                              "fabricante": "MERCUSYS"}
        registro.MercusysMW306R = Caido
        try:
            r = registro.conectar_router("192.168.1.1", Credenciales("admin", "temporal-123"))
        finally:
            registro.obtener_huella, registro.MercusysMW306R = original_huella, original_clase
        self.assertFalse(r["correcto"])
        self.assertIn("sin respuesta", r["error"])


class TestScriptDePrueba(unittest.TestCase):
    def test_argumentos(self):
        from scripts.probar_mw306r import construir_parser
        ap = construir_parser()
        self.assertIsNone(ap.parse_args(["192.168.1.1"]).canal)
        self.assertEqual(ap.parse_args(["192.168.1.1", "--canal", "6"]).canal, 6)
        with self.assertRaises(SystemExit):      # no se permiten dos acciones a la vez
            ap.parse_args(["192.168.1.1", "--canal", "6", "--bloquear", "AA:BB:CC:00:00:01"])

    def test_solo_lectura_contra_router_simulado(self):
        from scripts.probar_mw306r import mostrar_lectura
        a, _ = adaptador()
        self.assertEqual(len(mostrar_lectura(a)), 4)


if __name__ == "__main__":
    unittest.main()
