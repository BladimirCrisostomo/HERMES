"""Prueba controlada de HERMES contra TU Mercusys MW306R real.

Por defecto SOLO LEE (no cambia nada). Las acciones exigen un parámetro explícito,
pasan por el guardián (confirmación, protecciones, verificación y reversión) y
conviene hacerlas con la PC conectada POR CABLE al router.

  python -m scripts.probar_mw306r 192.168.1.1                     # solo lectura
  python -m scripts.probar_mw306r 192.168.1.1 --canal 6           # cambiar canal (0 = automático)
  python -m scripts.probar_mw306r 192.168.1.1 --bloquear AA:BB:CC:DD:EE:FF
  python -m scripts.probar_mw306r 192.168.1.1 --desbloquear AA:BB:CC:DD:EE:FF

Solo se pide la CONTRASEÑA del panel (este router no usa usuario). No se muestra al escribirla;
también puede leerse de HERMES_ROUTER_PASS.
"""
import argparse
import sys

from src import config, credenciales, dispositivos
from src.politicas import GuardianRouter, Modo, Verificador
from src.router.adapters.mercusys_mw306r import ErrorRouter, MercusysMW306R
from src.router.manager import RouterManager
from src.seguridad import exigir_ip_privada


def construir_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ip", help="IP del router (normalmente 192.168.1.1)")
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--canal", type=int, help="cambia el canal Wi-Fi (0 = automático)")
    grupo.add_argument("--bloquear", metavar="MAC")
    grupo.add_argument("--desbloquear", metavar="MAC")
    return ap


def preguntar(texto):
    return input(f"\n{texto} [s/N]: ").strip().lower() in ("s", "si", "sí", "y", "yes")


def mostrar_lectura(router):
    info = router.obtener_informacion()
    wifi = router.obtener_configuracion_wifi()
    canal = "automático" if wifi["canal"] == 0 else wifi["canal"]
    print(f"Router: {info['fabricante']} {info['modelo']}  |  IP {info['ip_lan']}")
    print(f"Wi-Fi:  red '{wifi['ssid']}', canal {canal}")
    print(f"Canales permitidos: {router.canales_permitidos()}")
    clientes = router.obtener_clientes()
    print(f"\nDispositivos conectados: {len(clientes)}")
    for c in clientes:
        estado = "BLOQUEADO" if c["bloqueado"] else ""
        print(f"  {c['ip'] or '?':<16}{c['mac']:<19}{(c['nombre'] or '-'):<24}{estado}")
    return clientes


def main(argv=None):
    args = construir_parser().parse_args(argv)
    config.configurar_logging()
    try:
        exigir_ip_privada(args.ip)
        cred = credenciales.desde_entorno() or credenciales.pedir_credenciales(args.ip, pedir_usuario=False)
        router = MercusysMW306R(args.ip, cred)
        print("AVISO:", credenciales.advertencia_transporte({"https": False}))
        router.conectar()
    except (ErrorRouter, OSError, ValueError) as error:
        sys.exit(f"No se pudo conectar: {error}")      # el mensaje nunca incluye la contraseña

    try:
        clientes = mostrar_lectura(router)
        accion = None
        if args.canal is not None:
            accion = ("cambiar_canal", args.canal)
        elif args.bloquear:
            accion = ("bloquear_cliente", args.bloquear.upper())
        elif args.desbloquear:
            accion = ("desbloquear_cliente", args.desbloquear.upper())
        if accion is None:
            print("\nSolo lectura: no se modificó nada.")
            return

        # Protecciones: este equipo y el propio router no se pueden bloquear.
        protegidos = dispositivos.macs_protegidas(dispositivos.escanear(gateway=args.ip))
        info_mac = router.obtener_informacion().get("mac_router")
        if info_mac:
            protegidos.add(info_mac)
        manager = RouterManager()
        manager.establecer_router(router)
        guardian = GuardianRouter(
            manager, Modo.CONFIRMAR, protegidos=protegidos,
            verificador=Verificador(gateway_ip=args.ip, host=config.HOST_PRUEBA))
        resultado = guardian.ejecutar(*accion, confirmar=preguntar)
        print(f"\nResultado: {resultado.motivo}")
        if resultado.ejecutada:
            mostrar_lectura(router)
    finally:
        router.desconectar()


if __name__ == "__main__":
    main()
