"""HERMES - Sistema inteligente de administración y diagnóstico de redes (consola).

Uso:  python app.py
"""
from src import config
from src.motor import procesar_consulta

SALIR = {"salir", "exit", "quit", "q"}


def mostrar(r):
    print(f"\nIntención detectada: {r.intencion}\n")

    if r.medicion is not None:
        m, d = r.medicion, r.diagnostico
        print(f"Equipo:   {r.red.get('equipo')}")
        print(f"IP local: {r.red.get('ip_local')}")
        print(f"Router:   {r.red.get('gateway') or 'no detectado'}")
        print(f"Internet: {'OK' if m.internet.conexion else 'SIN RESPUESTA'}", end="")
        if m.internet.conexion:
            print(f" | latencia {m.internet.latencia} ms | jitter {m.internet.jitter} ms"
                  f" | pérdida {m.internet.perdida}%", end="")
        print()
        if m.tiene_gateway and m.gateway.conexion:
            print(f"Router:   latencia {m.gateway.latencia} ms | pérdida {m.gateway.perdida}%")
        print(f"\nDiagnóstico:    {d.mensaje}")
        print(f"Recomendación:  {d.recomendacion}")
        origen = "modelo de ML" if d.origen == "ml" else "reglas"
        extra = f" (confianza {d.confianza:.0%})" if d.confianza is not None else ""
        print(f"\n[Fuente: {origen}{extra}]")
    elif r.intencion == "listar_dispositivos" and r.datos.get("dispositivos"):
        print(r.mensaje, "\n")
        print(f"{'IP':<16}{'MAC':<19}{'Fabricante':<18}{'Nombre':<24}Nota")
        for d in r.datos["dispositivos"]:
            nota = ", ".join(n for n, activo in (
                ("este equipo", d["es_este_equipo"]), ("router", d["es_gateway"]),
                ("MAC privada", d["mac_aleatoria"])) if activo)
            print(f"{d['ip']:<16}{(d['mac'] or '?'):<19}{(d['fabricante'] or '-'):<18}"
                  f"{(d['nombre'] or '-')[:22]:<24}{nota}")
    elif r.intencion == "info_router" and r.datos:
        print(r.mensaje)
        for k, v in r.datos.get("informacion", {}).items():
            print(f"  {k}: {v}")
        for k, v in r.datos.get("capacidades", {}).items():
            print(f"  {k}: {v}")
    elif r.intencion == "analizar_wifi" and r.datos.get("correcto"):
        print(r.mensaje)
        for canal, cant in r.datos["redes_por_canal"].items():
            print(f"  Canal {canal:2}: {'#' * cant} {cant}")
    else:
        print(r.mensaje)


def main():
    config.configurar_logging()
    print("=== HERMES ===")
    print("Sistema Inteligente de Administración y Diagnóstico de Redes")
    print("(escribe 'salir' para terminar)\n")
    while True:
        try:
            pregunta = input("¿Qué problema tienes con tu red?: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if pregunta.lower() in SALIR:
            break
        if not pregunta:
            continue
        print("\nAnalizando tu red, un momento...")
        mostrar(procesar_consulta(pregunta))
        print()


if __name__ == "__main__":
    main()
