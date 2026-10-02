#este archivo define la interfaz que deben implementar todos los routers compatibles con el sistema.
from abc import ABC, abstractmethod


class RouterInterface(ABC):

    @abstractmethod
    def conectar(self):
        """Establece conexión con el router."""
        pass

    @abstractmethod
    def desconectar(self):
        """Cierra la conexión con el router."""
        pass

    @abstractmethod
    def obtener_informacion(self):
        """Obtiene información básica del router."""
        pass

    @abstractmethod
    def obtener_capacidades(self):
        """Obtiene las capacidades disponibles del router."""
        pass

    @abstractmethod
    def obtener_clientes(self):
        """Obtiene los dispositivos conectados."""
        pass

    @abstractmethod
    def obtener_configuracion_wifi(self):
        """Obtiene la configuración Wi-Fi."""
        pass

    @abstractmethod
    def cambiar_canal(self, canal):
        """Cambia el canal Wi-Fi."""
        pass

    @abstractmethod
    def bloquear_cliente(self, identificador):
        """Bloquea un dispositivo."""
        pass

    @abstractmethod
    def desbloquear_cliente(self, identificador):
        """Desbloquea un dispositivo."""
        pass

    @abstractmethod
    def configurar_qos(self, configuracion):
        """Configura reglas de calidad de servicio."""
        pass