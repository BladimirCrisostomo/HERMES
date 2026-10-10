# profile.py
# Almacena y administra la información descubierta del router.

class RouterProfile:
    """
    Guarda la información recopilada sobre un router.
    """

    def __init__(self):
        # Diccionario donde se almacenan los datos del router.
        self.datos = {}

    def establecer(self, clave, valor):
        """
        Guarda un dato o actualiza su valor.
        """
        self.datos[clave] = valor

    def actualizar(self, nuevos_datos):
        """
        Guarda varios datos al mismo tiempo.
        """
        self.datos.update(nuevos_datos)

    def obtener(self, clave, valor_predeterminado=None):
        """
        Recupera un dato del perfil.
        """
        return self.datos.get(clave, valor_predeterminado)

    def mostrar(self):
        """
        Muestra toda la información almacenada.
        """
        print("=== PERFIL DEL ROUTER ===")

        if not self.datos:
            print("No hay información registrada.")
            return

        for clave, valor in self.datos.items():
            print(f"{clave}: {valor}")
