"""Prueba de humo de streamlit_app.py con un Streamlit SIMULADO (no necesita instalarlo).

Ejecuta el script completo y comprueba que no falle y que los flujos principales funcionen.
No sustituye a probar la interfaz en el navegador.
"""
import runpy
import sys
import types
import unittest

from src import asistente, config
from src.politicas import Modo

SCRIPT = str(config.RAIZ / "streamlit_app.py")


class Rerun(Exception):
    """Streamlit detiene el script con una excepción al llamar a st.rerun()."""


class Estado(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v):
        self[k] = v


class Contexto:
    def __init__(self, st):
        self._st = st

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __getattr__(self, nombre):
        return getattr(self._st, nombre)


class StreamlitFalso(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = Estado()
        self.salida = []            # todo el HTML/markdown escrito
        self.pulsados = set()       # claves de botones "pulsados" en esta ejecución
        self.entrada = None
        self.valores = {}           # valores de text_input por etiqueta

    def reiniciar_ejecucion(self, pulsados=(), entrada=None):
        self.salida, self.pulsados, self.entrada = [], set(pulsados), entrada

    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)

        def funcion(*args, **kw):
            for a in args[:1]:
                if isinstance(a, str):
                    self.salida.append(a)
            return None
        return funcion

    # --- contenedores ---
    sidebar = property(lambda self: Contexto(self))

    def form(self, *a, **k): return Contexto(self)
    def spinner(self, *a, **k): return Contexto(self)
    def expander(self, *a, **k): return Contexto(self)
    def chat_message(self, *a, **k): return Contexto(self)

    def columns(self, spec, **k):
        return [Contexto(self) for _ in range(spec if isinstance(spec, int) else len(spec))]

    def tabs(self, nombres):
        return [Contexto(self) for _ in nombres]

    # --- salida ---
    def markdown(self, texto, **k): self.salida.append(texto)

    # --- entradas ---
    def button(self, etiqueta, key=None, **k): return (key or etiqueta) in self.pulsados
    def form_submit_button(self, etiqueta, **k): return etiqueta in self.pulsados
    def text_input(self, etiqueta, value="", **k): return self.valores.get(etiqueta, value)
    def selectbox(self, etiqueta, opciones, index=0, **k): return opciones[index]
    def radio(self, etiqueta, opciones, index=0, **k): return opciones[index]
    def chat_input(self, *a, **k): return self.entrada
    def rerun(self): raise Rerun()


class TestInterfazWeb(unittest.TestCase):
    def setUp(self):
        self.st = StreamlitFalso()
        self._anterior = sys.modules.get("streamlit")
        sys.modules["streamlit"] = self.st

    def tearDown(self):
        if self._anterior is None:
            sys.modules.pop("streamlit", None)
        else:
            sys.modules["streamlit"] = self._anterior

    def ejecutar(self, **kw):
        self.st.reiniciar_ejecucion(**kw)
        try:
            runpy.run_path(SCRIPT)
        except Rerun:
            pass
        return "\n".join(str(x) for x in self.st.salida)

    def conectar_demo(self, modo=Modo.CONFIRMAR):
        ses, error, _ = asistente.conectar("192.168.100.1", simulacion=True, modo=modo)
        self.assertIsNone(error)
        self.st.session_state["sesion"] = ses
        return ses

    def test_primera_pantalla_sin_router(self):
        html = self.ejecutar()
        self.assertIn("HERMES", html)
        self.assertIn("estado-offline", html)
        self.assertIn("sin enlace", html)

    def test_boton_demo_abre_una_sesion_simulada(self):
        self.ejecutar(pulsados={"DEMO"})
        ses = self.st.session_state["sesion"]
        self.assertIsNotNone(ses)
        self.assertTrue(ses.simulado)

    def test_conectar_sin_contrasena_no_intenta_nada(self):
        self.st.valores["IP DEL ROUTER"] = "192.168.1.1"
        self.ejecutar(pulsados={"CONECTAR"})
        self.assertIsNone(self.st.session_state["sesion"])
        self.assertIn("contraseña", self.st.session_state["error_conexion"])

    def test_pantallas_con_router_muestran_dispositivos_y_registro(self):
        self.conectar_demo()
        self.ejecutar()                       # primera pasada: inicializa el estado
        self.st.session_state["clientes"] = self.st.session_state["sesion"].clientes()
        html = self.ejecutar()
        self.assertIn("estado-simulacion", html)
        self.assertIn("laptop-jose", html)
        self.assertIn("MODO SIMULACIÓN", html)

    def test_orden_en_el_chat_pide_confirmacion_y_luego_ejecuta(self):
        ses = self.conectar_demo()
        self.ejecutar(entrada="bloquea la consola")
        pendiente = self.st.session_state["pendiente"]
        self.assertEqual(pendiente["accion"], "bloquear_cliente")
        self.assertFalse(any(c["bloqueado"] for c in ses.clientes()))      # aún no se hizo nada
        html = self.ejecutar()
        self.assertIn("CONFIRMACIÓN REQUERIDA", html)
        self.ejecutar(pulsados={"confirmar_ok"})
        self.assertIsNone(self.st.session_state["pendiente"])
        self.assertTrue(next(c for c in ses.clientes() if c["mac"] == "AA:BB:CC:00:00:04")["bloqueado"])

    def test_cancelar_no_modifica_nada(self):
        ses = self.conectar_demo()
        self.ejecutar(entrada="bloquea la consola")
        self.ejecutar(pulsados={"confirmar_no"})
        self.assertIsNone(self.st.session_state["pendiente"])
        self.assertFalse(any(c["bloqueado"] for c in ses.clientes()))

    def test_modo_automatico_cambia_el_canal_sin_preguntar(self):
        ses = self.conectar_demo(Modo.AUTOMATICO)
        self.st.radio = lambda etiqueta, opciones, index=0, **k: "automatico"
        self.ejecutar(entrada="cambia el canal a 11")
        self.assertIsNone(self.st.session_state["pendiente"])
        self.assertEqual(ses.router.obtener_configuracion_wifi()["canal"], 11)

    def test_buscar_router_elige_el_unico_compatible(self):
        original = asistente.buscar_routers
        asistente.buscar_routers = lambda extra=(): [
            {"ip": "192.168.100.1", "adaptador": None, "servidor": "ISP", "titulo": "Modem"},
            {"ip": "192.168.1.1", "adaptador": "mercusys_mw306r", "servidor": "Boa", "titulo": "Mercusys"}]
        try:
            self.ejecutar(pulsados={"buscar_router"})
            self.assertEqual(self.st.session_state["ip_router"], "192.168.1.1")
            html = self.ejecutar()
        finally:
            asistente.buscar_routers = original
        self.assertIn("compatible", html)
        self.assertIn("no compatible", html)

    def test_buscar_router_sin_compatibles_no_cambia_la_ip(self):
        original = asistente.buscar_routers
        asistente.buscar_routers = lambda extra=(): [
            {"ip": "192.168.100.1", "adaptador": None, "servidor": "ISP", "titulo": "Modem"}]
        try:
            self.ejecutar()
            ip_antes = self.st.session_state["ip_router"]
            self.ejecutar(pulsados={"buscar_router"})
        finally:
            asistente.buscar_routers = original
        self.assertEqual(self.st.session_state["ip_router"], ip_antes)

    def test_boton_rapido_encola_una_consulta(self):
        self.conectar_demo()
        self.ejecutar(pulsados={"rapido_disp"})
        textos = [t.texto for t in self.st.session_state["historial"] if t.rol == "hermes"]
        self.assertTrue(any("dispositivos" in t for t in textos))


if __name__ == "__main__":
    unittest.main()
