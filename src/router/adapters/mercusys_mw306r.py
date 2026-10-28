"""Adaptador para el Mercusys MW306R (V1), basado en capturas reales del panel.

PROTOCOLO (deducido de las capturas del panel web, no documentado por el fabricante):
  POST http://<router>/?code=<N>&asyn=<M>&id=<sesión>   cuerpo: texto plano
    code=2  leer objetos       cuerpo "13|1,0,0#9|1,0,0"  ('#' separa objetos)
    code=1  escribir objetos   cuerpo "id 32|1,0,0\\r\\nclave valor\\r\\n..."
    code=0  comando            cuerpo "wlan channelList 2g", "advanced bm -add ..."
  La respuesta empieza con "00000" si todo salió bien.
  Objetos conocidos: 13 = clientes (ip/mac), 9 = nombres DHCP (hostName/mac),
  32 = radio Wi-Fi (uChannel; 0 = automático), 33 = SSID principal,
  58 = control de acceso (ctrlEnable, isWhiteList), 73 = lista negra (devName/mac).

LOGIN (deducido del JavaScript del propio panel): no hay sesión ni cookie. El `id` de CADA
petición es la contraseña cifrada: id = cifrar(CLAVE, contraseña, TABLA).
authInfo lo entrega el router sin credenciales en la respuesta 401 de `POST /?code=2&asyn=1`
(la misma petición que hace el panel justo antes de enviar la contraseña).
El cifrado (su.encrypt) es una sustitución XOR reversible: el id equivale a la contraseña.
Por eso el id se trata como secreto y no se escribe nunca en logs ni mensajes de error.

ESTADO: login, lectura de clientes, canal, bloqueo y desbloqueo implementados a partir de
capturas. FALTAN el módulo QoS (límite por dispositivo) y el reinicio. Todo está probado con
un router simulado; NADA se ha ejecutado todavía contra el router real.

SEGURIDAD: las escrituras reenvían la configuración completa (incluida la clave Wi-Fi);
esos valores se registran como secretos y nunca se escriben en los logs.
"""
import logging
import re
from urllib.parse import quote

from ...seguridad import registrar_secreto, validar_mac
from .. import http_client
from ..capabilities import CONFIRMADA, NO_VERIFICADA
from ..interface import RouterController

log = logging.getLogger("hermes.router.mw306r")

CLAVES_SECRETAS = ("authKey", "cPskSecret", "cUsrPIN", "cRadiusSecret", "cPassWD")
_NOMBRE_SEGURO = re.compile(r"[^A-Za-z0-9._-]")


class ErrorRouter(RuntimeError):
    """El router respondió con un código distinto de 00000."""


# --------------------------------------------------------------------------- parseo
def _codigo(texto):
    return texto.replace("\r", "").split("\n")[0].strip()


def parsear_respuesta(texto):
    """Respuesta de lectura -> {id_objeto: {clave: [resto_de_linea, ...]}} (en orden)."""
    if _codigo(texto) != "00000":
        raise ErrorRouter(f"Código de error del router: {_codigo(texto) or 'vacío'}")
    objetos, actual = {}, None
    for linea in texto.replace("\r", "").split("\n")[1:]:
        if not linea:
            continue
        clave, _, resto = linea.partition(" ")
        if clave == "id":
            actual = objetos.setdefault(resto.strip(), {})
        elif actual is not None:
            actual.setdefault(clave, []).append(resto)
            if clave in CLAVES_SECRETAS:
                registrar_secreto(resto)
    return objetos


def escalar(objeto, clave, defecto=None):
    valores = objeto.get(clave)
    return valores[0] if valores else defecto


def indexado(objeto, clave):
    """Entradas 'clave <n> <valor>' -> {n: valor}."""
    salida = {}
    for resto in objeto.get(clave, []):
        indice, _, valor = resto.partition(" ")
        if indice.isdigit():
            salida[int(indice)] = valor
    return salida


def _mac_normal(mac):
    return mac.replace("-", ":").upper()


def _mac_valida(mac):
    return bool(mac) and mac.replace("-", "").replace(":", "").strip("0") != ""


def extraer_clientes(clientes_13, nombres_9, lista_negra_73):
    """Une los objetos 13 (ip/mac), 9 (nombres) y 73 (lista negra) en una lista de clientes."""
    nombres = {}
    macs9, hosts9 = indexado(nombres_9, "mac"), indexado(nombres_9, "hostName")
    for i, mac in macs9.items():
        if _mac_valida(mac):
            nombres[_mac_normal(mac)] = hosts9.get(i, "")
    bloqueados = {_mac_normal(m) for m in indexado(lista_negra_73, "mac").values() if _mac_valida(m)}
    ips, macs = indexado(clientes_13, "ip"), indexado(clientes_13, "mac")
    clientes = []
    for i in sorted(macs):
        if not _mac_valida(macs[i]):
            continue
        mac, ip = _mac_normal(macs[i]), ips.get(i)
        clientes.append({
            "mac": mac, "ip": ip if ip and ip != "0.0.0.0" else None,
            "nombre": nombres.get(mac) or None,
            "consumo_kbps": None,          # este modelo no informa consumo por cliente
            "bloqueado": mac in bloqueados, "limite_kbps": None,
        })
    return clientes


def parsear_canales(texto):
    """Respuesta de 'wlan channelList 2g' -> [1, 2, ..., 11] (sin el 0 = automático)."""
    if _codigo(texto) != "00000":
        raise ErrorRouter(f"Código de error del router: {_codigo(texto)}")
    resto = " ".join(texto.replace("\r", "").split("\n")[1:])
    return [int(n) for n in resto.split() if n.isdigit() and int(n) > 0]


# ------------------------------------------------------------------------ construcción
def serializar_objeto(id_objeto, objeto, cambios=None):
    """Objeto leído -> texto para escribir ('id ...' + líneas), aplicando `cambios`.

    Reproduce el orden de las capturas: uKeyLength n / cKeyVal n van intercalados,
    justo después de uPskGKUpdateIntvl.
    """
    cambios = cambios or {}
    lineas = [f"id {id_objeto}"]
    for clave in (k for k in objeto if k not in ("uKeyLength", "cKeyVal")):
        for resto in objeto[clave]:
            lineas.append(f"{clave} {cambios[clave]}" if clave in cambios else f"{clave} {resto}")
        if clave == "uPskGKUpdateIntvl":
            for largo, valor in zip(objeto.get("uKeyLength", []), objeto.get("cKeyVal", [])):
                lineas.append(f"uKeyLength {largo}")
                lineas.append(f"cKeyVal {valor}")
    return "\r\n".join(lineas) + "\r\n"


def cifrar(t, r, tabla):
    """Port de `$.su.encrypt` del panel (tpEncrypt.new.js): sustitución XOR contra una tabla.

    t = authInfo[3], r = contraseña, tabla = authInfo[4]. Sale max(len(t), len(r)) caracteres.
    """
    resultado, n = [], max(len(t), len(r))
    for c in range(n):
        u = f = 187
        if len(t) <= c:
            f = ord(r[c])
        elif len(r) <= c:
            u = ord(t[c])
        else:
            u, f = ord(t[c]), ord(r[c])
        resultado.append(tabla[(u ^ f) % len(tabla)])
    return "".join(resultado)


def codificar_para_url(texto):
    """Equivale a encodeURIComponent de JavaScript (deja ! * ' ( ) ~ sin codificar)."""
    return quote(texto, safe="!*'()~")


def comando_desbloquear(mac):
    """'advanced bm rule -del list:black mac:<MAC-CON-GUIONES>' (visto en la captura F)."""
    return f"advanced bm rule -del list:black mac:{validar_mac(mac).replace(':', '-')}"


def comando_bloquear(mac, nombre):
    """'advanced bm -add list:black name:<n> mac:<MAC-CON-GUIONES>' (todo validado)."""
    mac = validar_mac(mac).replace(":", "-")
    nombre = _NOMBRE_SEGURO.sub("_", nombre or "HERMES")[:32] or "HERMES"
    return f"advanced bm -add list:black name:{nombre} mac:{mac}"


def responde_al_protocolo(ip, transporte=None):
    """True si el equipo habla el protocolo de este panel: `POST /?code=7&asyn=1` sin
    credenciales responde 401 con los parámetros de login (≥4 líneas). Es una huella mucho
    más fiable que buscar la marca en el HTML. No cambia nada en el equipo."""
    transporte = transporte or (
        lambda ruta, cuerpo: http_client.enviar_texto_estado(ip, ruta, cuerpo, timeout=3))
    try:
        estado, texto = transporte("/?code=7&asyn=1", "")
    except OSError:
        return False
    return estado == 401 and len(texto.replace("\r", "").rstrip("\n").split("\n")) >= 4


# --------------------------------------------------------------------------- adaptador
class MercusysMW306R(RouterController):
    def __init__(self, ip, credenciales=None, transporte=None):
        self.ip = ip
        self._cred = credenciales
        self._sesion = None
        self.pasos_login = {}
        # transporte(ruta, cuerpo) -> (código_http, texto). Se sustituye en las pruebas.
        self._transporte = transporte or (
            lambda ruta, cuerpo: http_client.enviar_texto_estado(ip, ruta, cuerpo))

    # --- bajo nivel ---------------------------------------------------------
    def _enviar(self, code, asyn, cuerpo):
        if self._sesion is None:
            raise ErrorRouter("No hay sesión iniciada.")
        estado, texto = self._transporte(f"/?code={code}&asyn={asyn}&id={self._sesion}", cuerpo)
        if estado != 200:        # nunca se incluye la URL: lleva la contraseña cifrada
            raise ErrorRouter(f"El router respondió HTTP {estado}.")
        return texto

    def _leer(self, *ids):
        """`ids` son identificadores COMPLETOS de objeto, p. ej. '13|1,0,0' o '33|1,1,0'."""
        return parsear_respuesta(self._enviar(2, 1, "#".join(ids)))

    def _exigir_ok(self, respuesta, mensaje):
        if _codigo(respuesta) != "00000":
            raise ErrorRouter(mensaje)

    # --- sesión -------------------------------------------------------------
    def _parametros_login(self):
        """Replica al panel: justo antes de iniciar sesión pide `?code=2&asyn=1` (getLoginParams).

        El router responde 401 y en el cuerpo entrega líneas con los parámetros de cifrado.
        Estructura OBSERVADA en un MW306R real (largos): [5, 5, 5, 32, 255, 5] =
        [código, ?, ?, CLAVE de 32, TABLA de 255, ?]. La tabla es siempre la línea más larga y
        la clave la línea inmediatamente anterior; así no se depende de si hay una línea de
        código al principio (en una primera versión se tomaron las líneas 3 y 4 y el login
        fallaba siempre).
        """
        estado, texto = self._transporte("/?code=2&asyn=1", "")
        lineas = texto.replace("\r", "").rstrip("\n").split("\n")
        self.pasos_login["1_parametros"] = {"http": estado, "lineas": len(lineas),
                                            "largos": [len(l) for l in lineas][:8]}
        if estado != 401 or len(lineas) < 2:
            raise ErrorRouter("El router no respondió como un MW306R esperaba (parámetros de login).")
        indice = max(range(len(lineas)), key=lambda i: len(lineas[i]))
        if indice < 1 or len(lineas[indice]) < 32 or not lineas[indice - 1]:
            raise ErrorRouter("Los parámetros de login del router tienen un formato inesperado.")
        self.pasos_login["1_parametros"]["indice_tabla"] = indice
        return lineas[indice - 1], lineas[indice]

    def conectar(self):
        """Un solo intento de login. Los pasos quedan en `pasos_login` (sin secretos)."""
        self.pasos_login = {}
        if self._cred is None or not self._cred.contrasena:
            raise ErrorRouter("Se necesita la contraseña de administrador del router.")
        if len(self._cred.contrasena) > 32:
            raise ErrorRouter("El panel del MW306R no admite contraseñas de más de 32 caracteres.")
        clave, tabla = self._parametros_login()
        cifrado = cifrar(clave, self._cred.contrasena, tabla)
        sesion = codificar_para_url(cifrado)
        registrar_secreto(cifrado)
        registrar_secreto(sesion)

        estado, texto = self._transporte(f"/?code=7&asyn=0&id={sesion}", "")
        self.pasos_login["2_login"] = {"http": estado, "largo_cuerpo": len(texto),
                                       "primera_linea": _codigo(texto)[:12]}
        if estado == 401:
            raise ErrorRouter("El router rechazó la contraseña (HTTP 401).")
        if estado != 200:
            raise ErrorRouter(f"El router respondió HTTP {estado} al iniciar sesión.")
        # El cuerpo de un login correcto no se conoce con certeza: la prueba definitiva es
        # poder leer un dato protegido.
        self._sesion = sesion
        try:
            modelo = self._leer("0|1,0,0").get("0|1,0,0", {})
        except (ErrorRouter, OSError) as error:
            self._sesion = None
            self.pasos_login["3_lectura"] = {"error": str(error)[:80]}
            raise ErrorRouter("El router rechazó la contraseña.") from None
        self.pasos_login["3_lectura"] = {"modelo": escalar(modelo, "modelName")}
        if escalar(modelo, "modelName") != "MW306R":
            self._sesion = None
            raise ErrorRouter("Este adaptador solo está validado con el Mercusys MW306R.")
        log.info("Sesión iniciada en el MW306R (%s).", escalar(modelo, "softVer", "?"))

    def desconectar(self):
        self._sesion = None

    # --- lectura ------------------------------------------------------------
    def obtener_informacion(self):
        o = self._leer("1|1,0,0", "4|1,0,0")
        mac = indexado(o.get("1|1,0,0", {}), "mac").get(0, "")
        return {"fabricante": "MERCUSYS", "modelo": "MW306R",
                "ip_lan": escalar(o.get("4|1,0,0", {}), "ip"),
                "mac_router": _mac_normal(mac) if _mac_valida(mac) else None}

    def obtener_capacidades(self):
        return {
            "obtener_clientes": CONFIRMADA,       # vista en capturas B y D
            "cambiar_canal_wifi": CONFIRMADA,     # vista en captura C
            "bloquear_cliente": CONFIRMADA,       # bloqueo y desbloqueo vistos en capturas D y F
            "limitar_cliente": NO_VERIFICADA,     # el menú del panel tiene 'qos': falta capturarlo
            "reiniciar": NO_VERIFICADA,
        }

    def obtener_clientes(self):
        o = self._leer("13|1,0,0", "9|1,0,0", "73|1,0,0")
        return extraer_clientes(o.get("13|1,0,0", {}), o.get("9|1,0,0", {}), o.get("73|1,0,0", {}))

    def obtener_configuracion_wifi(self):
        o = self._leer("32|1,0,0", "33|1,1,0")
        canal = escalar(o.get("32|1,0,0", {}), "uChannel")
        return {"canal": int(canal) if canal and canal.isdigit() else None,
                "ssid": escalar(o.get("33|1,1,0", {}), "cSsid")}

    def canales_permitidos(self):
        return parsear_canales(self._enviar(0, 0, "wlan channelList 2g"))

    def _lista_negra(self):
        o = self._leer("73|1,0,0")["73|1,0,0"]
        return {_mac_normal(m) for m in indexado(o, "mac").values() if _mac_valida(m)}

    def _control_acceso(self):
        o = self._leer("58|1,0,0")["58|1,0,0"]
        return escalar(o, "ctrlEnable") == "1", escalar(o, "isWhiteList") == "1"

    # --- acciones -----------------------------------------------------------
    def cambiar_canal(self, canal):
        if canal != 0 and canal not in self.canales_permitidos():
            raise ValueError(f"El canal {canal} no está permitido en la región de este router.")
        o = self._leer("32|1,0,0", "33|1,1,0")
        texto = (serializar_objeto("32|1,0,0", o["32|1,0,0"], {"uChannel": str(canal)})
                 + serializar_objeto("33|1,1,0", o["33|1,1,0"]))
        self._exigir_ok(self._enviar(1, 0, texto), "El router rechazó el cambio de canal.")
        if self.obtener_configuracion_wifi()["canal"] != canal:     # verifica lo escrito
            raise ErrorRouter("El router no aplicó el canal solicitado.")
        log.warning("Canal Wi-Fi cambiado a %s.", "automático" if canal == 0 else canal)

    def bloquear_cliente(self, mac):
        activo, lista_blanca = self._control_acceso()
        if not activo or lista_blanca:
            raise ErrorRouter("El control de acceso está desactivado o en modo lista blanca; "
                              "HERMES no lo cambia por su cuenta.")
        nombre = next((c["nombre"] for c in self.obtener_clientes() if c["mac"] == mac), None)
        self._exigir_ok(self._enviar(0, 0, comando_bloquear(mac, nombre)), "El router rechazó el bloqueo.")
        if _mac_normal(validar_mac(mac)) not in self._lista_negra():     # verifica lo escrito
            raise ErrorRouter("El router no registró el bloqueo.")
        log.warning("Dispositivo bloqueado: %s", mac)

    def desbloquear_cliente(self, mac):
        self._exigir_ok(self._enviar(0, 0, comando_desbloquear(mac)), "El router rechazó el desbloqueo.")
        if _mac_normal(validar_mac(mac)) in self._lista_negra():
            raise ErrorRouter("El router no quitó el bloqueo.")
        log.warning("Dispositivo desbloqueado: %s", mac)

    def limitar_cliente(self, mac, kbps):
        raise NotImplementedError("Falta capturar el módulo QoS del panel (límite de velocidad).")

    def quitar_limite(self, mac):
        raise NotImplementedError("Falta capturar el módulo QoS del panel (límite de velocidad).")

    def reiniciar(self):
        raise NotImplementedError("Falta capturar el reinicio del panel.")
