from profile import RouterProfile


def main():

    perfil = RouterProfile()

    perfil.establecer(
        "ip",
        "192.168.100.1"
    )

    perfil.establecer(
        "servidor_web",
        "Boa/0.93.15"
    )

    perfil.establecer(
        "fabricante",
        "Realtek Semiconductor Corp."
    )

    perfil.establecer(
        "panel_administracion",
        "/admin/login.asp"
    )

    perfil.establecer(
        "http",
        True
    )

    perfil.establecer(
        "https",
        False
    )

    perfil.mostrar()


if __name__ == "__main__":
    main()
    