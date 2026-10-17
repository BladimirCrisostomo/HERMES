"""Contratos que deben cumplir los adaptadores de router.

La interfaz está dividida a propósito (README: 'separación entre diagnóstico
y funciones que modifican la red'):

  RouterReader     -> solo lectura. Es lo único que usa el diagnóstico.
  RouterController -> además puede MODIFICAR el router. Nunca se llama
                      directamente: pasa por RouterManager / GuardianRouter,
                      que validan, piden confirmación, verifican y registran.

Formato esperado de obtener_clientes(): lista de dicts con las claves
  mac, ip, nombre, consumo_kbps, bloqueado (bool), limite_kbps (int | None)
Formato de obtener_configuracion_wifi(): dict con al menos 'canal' (int).
"""
from abc import ABC, abstractmethod


class RouterReader(ABC):
    @abstractmethod
    def conectar(self): ...

    @abstractmethod
    def desconectar(self): ...

    @abstractmethod
    def obtener_informacion(self): ...

    @abstractmethod
    def obtener_capacidades(self):
        """dict {nombre_capacidad: 'confirmada' | 'no_verificada' | 'no_detectada'}"""

    @abstractmethod
    def obtener_clientes(self): ...

    @abstractmethod
    def obtener_configuracion_wifi(self): ...


class RouterController(RouterReader):
    @abstractmethod
    def cambiar_canal(self, canal): ...

    @abstractmethod
    def bloquear_cliente(self, mac): ...

    @abstractmethod
    def desbloquear_cliente(self, mac): ...

    @abstractmethod
    def limitar_cliente(self, mac, kbps): ...

    @abstractmethod
    def quitar_limite(self, mac): ...

    @abstractmethod
    def reiniciar(self): ...
