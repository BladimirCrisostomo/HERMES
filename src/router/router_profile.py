"""Almacena la información descubierta de un router."""


class RouterProfile:
    def __init__(self):
        self.datos = {}

    def establecer(self, clave, valor):
        self.datos[clave] = valor

    def actualizar(self, nuevos_datos):
        self.datos.update(nuevos_datos)

    def obtener(self, clave, valor_predeterminado=None):
        return self.datos.get(clave, valor_predeterminado)

    def mostrar(self):
        print("=== PERFIL DEL ROUTER ===")
        if not self.datos:
            print("No hay información registrada.")
            return
        for clave, valor in self.datos.items():
            print(f"{clave}: {valor}")
