#esto es lo que se encarga de detectar las capacidades del router, es decir, qué servicios están disponibles y cuáles no. 
class RouterCapabilities:

    def __init__(self):
        self.capacidades = {}

    def establecer(self, nombre, disponible):
        """
        Registra si una capacidad está disponible.
        """
        self.capacidades[nombre] = disponible

    def disponible(self, nombre):
        """
        Comprueba si una capacidad está disponible.
        """
        return self.capacidades.get(nombre, False)

    def obtener_todas(self):
        """
        Devuelve todas las capacidades conocidas.
        """
        return self.capacidades

    def mostrar(self):
        """
        Muestra las capacidades del router.
        """

        print("=== CAPACIDADES DE HERMES ===")

        for nombre, disponible in self.capacidades.items():

            estado = "DISPONIBLE" if disponible else "NO DISPONIBLE"

            print(f"{nombre}: {estado}")