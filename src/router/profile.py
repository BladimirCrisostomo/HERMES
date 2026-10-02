#este archivo se encarga de almacenar información descubierta del router, como fabricante, modelo, versión de firmware, etc.
class RouterProfile:

    def __init__(self):
        self.informacion = {}

    def establecer(self, nombre, valor):
        """
        Guarda información descubierta del router.
        """
        self.informacion[nombre] = valor

    def obtener(self, nombre):
        """
        Obtiene un dato específico del perfil.
        """
        return self.informacion.get(nombre)

    def obtener_todo(self):
        """
        Devuelve todo el perfil.
        """
        return self.informacion

    def mostrar(self):
        """
        Muestra el perfil del router.
        """

        print("=== PERFIL DEL ROUTER ===")

        for nombre, valor in self.informacion.items():
            print(f"{nombre}: {valor}")