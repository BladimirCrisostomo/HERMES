"""PLANTILLA para crear el adaptador de un router real.  (No se registra sola.)

Pasos:
 1. Copia este archivo (p. ej. adapters/mercusys_mw306r.py).
 2. Implementa los métodos con las peticiones reales de ese panel. La forma de
    averiguarlas: abre el panel, F12 -> Network, haz la acción a mano y copia la
    petición (URL, método, campos). NO incluyas tu contraseña al compartirlas.
 3. En obtener_capacidades() marca como 'confirmada' SOLO lo que hayas probado
    de verdad. Las acciones de HERMES se niegan a ejecutar lo que no esté confirmado.
 4. Registra el adaptador en src/router/registro.py con su función `puntuar`.
"""
from ..capabilities import CONFIRMADA, NO_VERIFICADA
from ..interface import RouterController


class AdaptadorPlantilla(RouterController):
    def __init__(self, ip, credenciales):
        self.ip = ip
        self._cred = credenciales          # nunca imprimir ni registrar la contraseña

    def conectar(self):
        raise NotImplementedError("Iniciar sesión en el panel del router.")

    def desconectar(self):
        raise NotImplementedError("Cerrar la sesión (importante: algunos routers solo admiten una).")

    def obtener_informacion(self):
        raise NotImplementedError

    def obtener_capacidades(self):
        return {"obtener_clientes": NO_VERIFICADA, "cambiar_canal_wifi": NO_VERIFICADA,
                "bloquear_cliente": NO_VERIFICADA, "limitar_cliente": NO_VERIFICADA,
                "reiniciar": NO_VERIFICADA}

    def obtener_clientes(self):
        raise NotImplementedError("Devolver dicts con mac, ip, nombre, consumo_kbps, bloqueado, limite_kbps.")

    def obtener_configuracion_wifi(self):
        raise NotImplementedError("Devolver al menos {'canal': int}.")

    def cambiar_canal(self, canal): raise NotImplementedError
    def bloquear_cliente(self, mac): raise NotImplementedError
    def desbloquear_cliente(self, mac): raise NotImplementedError
    def limitar_cliente(self, mac, kbps): raise NotImplementedError
    def quitar_limite(self, mac): raise NotImplementedError
    def reiniciar(self): raise NotImplementedError
