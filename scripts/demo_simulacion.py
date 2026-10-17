"""Demostración SEGURA: HERMES administrando un router simulado (no toca ningún router real).

Uso:  python -m scripts.demo_simulacion

Muestra los tres modos, las protecciones, el límite de cambios y la reversión
automática cuando la red deja de responder.
"""
from src.politicas import GuardianRouter, Modo
from src.router.manager import RouterManager
from src.router.registro import conectar_router

PROPIO = "AA:BB:CC:00:00:01"   # "este equipo" en la simulación


class RedCaida:
    """Verificador de mentira: simula que la red deja de responder tras el cambio."""
    def antes(self): pass
    def despues(self): return False


class RedSana(RedCaida):
    def despues(self): return True


def mostrar(titulo, resultado):
    estado = "REVERTIDO" if resultado.revertida else ("OK" if resultado.ejecutada else "NO")
    print(f"  [{estado}] {titulo}: {resultado.motivo}")


def main():
    conexion = conectar_router("192.168.100.1", simulacion=True)
    router, manager = conexion["router"], RouterManager()
    manager.establecer_router(router)
    print(conexion["advertencias"][0], "\n")

    print("Clientes conectados:")
    for c in router.obtener_clientes():
        print(f"  {c['nombre']:<14}{c['mac']}  {c['consumo_kbps']:>6} kbps")
    mas_pesado = max(router.obtener_clientes(), key=lambda c: c["consumo_kbps"])
    print(f"\nQuien más consume: {mas_pesado['nombre']} ({mas_pesado['consumo_kbps']} kbps)\n")

    print("1) Modo SUGERIR: solo propone")
    g = GuardianRouter(manager, Modo.SUGERIR, protegidos=[PROPIO], verificador=RedSana())
    mostrar("limitar consola", g.ejecutar("limitar_cliente", ("AA:BB:CC:00:00:04", 2000)))

    print("\n2) Modo CONFIRMAR: pregunta antes (aquí el usuario responde 'sí')")
    g = GuardianRouter(manager, Modo.CONFIRMAR, protegidos=[PROPIO], verificador=RedSana())
    mostrar("limitar consola", g.ejecutar("limitar_cliente", ("AA:BB:CC:00:00:04", 2000), lambda t: True))

    print("\n3) Protección: no deja bloquear este equipo")
    mostrar("bloquear laptop-jose", g.ejecutar("bloquear_cliente", PROPIO, lambda t: True))

    print("\n4) AUTOMÁTICO: cambia de canal solo, pero la red se cae -> se revierte")
    g = GuardianRouter(manager, Modo.AUTOMATICO, verificador=RedCaida(),
                       espera_verificacion=0, dormir=lambda s: None)
    mostrar("cambiar a canal 11", g.ejecutar("cambiar_canal", 11))
    print(f"     Canal actual del router simulado: {router.obtener_configuracion_wifi()['canal']} (volvió al original)")

    print("\n5) AUTOMÁTICO no bloquea sin preguntar: exige confirmación")
    g = GuardianRouter(manager, Modo.AUTOMATICO, protegidos=[PROPIO], verificador=RedSana())
    mostrar("bloquear desconocido (sin confirmar)", g.ejecutar("bloquear_cliente", "AA:BB:CC:00:00:05"))

    print("\nTodo ocurrió en simulación: ningún router real fue modificado.")


if __name__ == "__main__":
    main()
