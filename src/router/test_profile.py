
import sys
from pathlib import Path

# Obtener la carpeta principal del proyecto HERMES.
CARPETA_PROYECTO = Path(__file__).resolve().parents[2]

# Agregar la carpeta principal a las rutas de búsqueda.
sys.path.insert(0, str(CARPETA_PROYECTO))

# Importar la clase desde nuestro archivo, no desde el módulo estándar.
from src.router.router_profile import RouterProfile


def main():
    perfil = RouterProfile()

    perfil.establecer("ip", "192.168.100.1")
    perfil.establecer("servidor_web", "Boa/0.93.15")
    perfil.establecer("fabricante", "Realtek Semiconductor Corp.")
    perfil.establecer("panel_administracion", "/admin/login.asp")
    perfil.establecer("http", True)
    perfil.establecer("https", False)

    perfil.mostrar()


if __name__ == "__main__":
    main()
