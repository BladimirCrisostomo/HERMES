"""HERMES · interfaz web estilo HUD.        Uso:  streamlit run streamlit_app.py

Toda la lógica vive en src/ (asistente.py, motor.py, politicas.py); este archivo solo dibuja.
"""
import time
from dataclasses import asdict

import streamlit as st

from src import asistente, config, dispositivos, discovery, ui_tema as ui
from src.asistente import Turno
from src.politicas import Modo

config.configurar_logging()
st.set_page_config(page_title="HERMES // Núcleo de red", page_icon="📡", layout="wide")
st.markdown(ui.TEMA_CSS, unsafe_allow_html=True)

MODOS = {
    "sugerir": "HERMES solo propone: no ejecuta nada.",
    "confirmar": "Pide tu confirmación antes de cada cambio.",
    "automatico": "Cambia canal y límites sin preguntar. Bloquear siempre pide confirmación.",
}
ESTADO_INICIAL = {
    "sesion": None, "historial": [], "pendiente": None, "registro": [], "clientes": [],
    "info": {}, "wifi": {}, "canales": [], "escaneo": None, "error_conexion": None, "diag_login": None,
    "hallazgos": [],
}


def iniciar():
    s = st.session_state
    for clave, valor in ESTADO_INICIAL.items():
        if clave not in s:
            s[clave] = list(valor) if isinstance(valor, list) else dict(valor) if isinstance(valor, dict) else valor
    if "limitador" not in s:
        s["limitador"] = asistente.LimitadorIntentos()
    if "ip_router" not in s:
        s["ip_router"] = discovery.obtener_gateway() or "192.168.1.1"


# ------------------------------------------------------------------ acciones sobre el router
def refrescar():
    s, ses = st.session_state, st.session_state.sesion
    if ses is None:
        return
    try:
        s.clientes = ses.clientes()
        s.wifi = ses.router.obtener_configuracion_wifi()
    except Exception as error:                       # sesión vencida o router sin respuesta
        s.error_conexion = f"Se perdió el enlace con el router: {error}"


def ejecutar_y_registrar(accion, valor, descripcion, confirmado):
    s, ses = st.session_state, st.session_state.sesion
    with st.spinner("Ejecutando y verificando la red…"):
        r = asistente.ejecutar(ses, accion, valor, confirmado)
    icono = "↩" if r.revertida else "✔" if r.ejecutada else "✖"
    s.registro.insert(0, (time.strftime("%H:%M:%S"), descripcion, f"{icono} {r.motivo}"))
    s.historial.append(Turno("hermes", f"**{descripcion}** → {icono} {r.motivo}"))
    refrescar()


def solicitar(accion, valor, descripcion):
    s = st.session_state
    if asistente.requiere_confirmacion(s.sesion, accion):
        s.pendiente = {"accion": accion, "valor": valor, "descripcion": descripcion}
        s.historial.append(Turno("hermes", "Necesito tu confirmación para continuar."))
    else:
        ejecutar_y_registrar(accion, valor, descripcion, False)


def procesar(texto):
    s = st.session_state
    s.historial.append(Turno("usuario", texto))
    with st.spinner("HERMES analizando…"):
        turno = asistente.atender(texto, s.sesion)
    s.historial.append(turno)
    if turno.orden:
        solicitar(turno.orden.accion, turno.orden.valor, turno.orden.descripcion)


# ------------------------------------------------------------------------------ barra lateral
def abrir_sesion(ip, contrasena, simulacion):
    s = st.session_state
    with st.spinner("Estableciendo enlace…"):
        ses, error, diag = asistente.conectar(ip, contrasena, simulacion, Modo.CONFIRMAR)
    if ses is None:
        s.limitador.registrar_fallo()
        s.error_conexion, s.diag_login = error, diag
        return
    s.limitador.registrar_exito()
    s.sesion, s.error_conexion, s.diag_login = ses, None, None
    s.info = ses.router.obtener_informacion()
    s.canales = (ses.router.canales_permitidos() if hasattr(ses.router, "canales_permitidos")
                 else list(range(1, 12)))
    refrescar()
    s.historial.append(Turno("hermes", "Enlace establecido. Puedes pedirme, por ejemplo: "
                                       "«cuántos dispositivos hay», «bloquea el celular», «cambia el canal a 6»."))
    st.rerun()


def barra_lateral():
    s = st.session_state
    with st.sidebar:
        st.markdown("### NÚCLEO")
        if s.sesion is None:
            st.markdown(ui.chip("sin enlace", "bad"), unsafe_allow_html=True)
            if st.button("BUSCAR MI ROUTER", key="buscar_router"):
                with st.spinner("Buscando routers compatibles…"):
                    s.hallazgos = asistente.buscar_routers([s.ip_router])
                compatibles = [h for h in s.hallazgos if h["adaptador"]]
                if len(compatibles) == 1:
                    s.ip_router = compatibles[0]["ip"]
                st.rerun()
            for h in s.hallazgos:
                etiqueta = ui.chip("compatible", "ok") if h["adaptador"] else ui.chip("no compatible", "warn")
                st.markdown(etiqueta + ui.chip(h["ip"]) + f'<span class="dato">{ui.esc(str(h["titulo"] or ""))[:30]}</span>',
                            unsafe_allow_html=True)
            if s.hallazgos and not any(h["adaptador"] for h in s.hallazgos):
                st.caption("Ninguno es compatible. Conéctate al Wi-Fi o al cable de tu Mercusys y vuelve a buscar.")
            with st.form("conexion", clear_on_submit=True):
                ip = st.text_input("IP DEL ROUTER", value=s.ip_router)
                clave = st.text_input("CONTRASEÑA DEL PANEL", type="password")
                c1, c2 = st.columns(2)
                conectar = c1.form_submit_button("CONECTAR", type="primary")
                demo = c2.form_submit_button("DEMO")
            st.caption("Contraseña = la de mwlogin.net (no la del Wi-Fi). No se guarda. DEMO = router simulado.")
            if demo:
                abrir_sesion("192.168.100.1", "", True)
            elif conectar:
                s.ip_router = ip.strip()
                if not s.limitador.puede_intentar():
                    s.error_conexion = f"Demasiados intentos. Espera {s.limitador.segundos_restantes()} s."
                elif not clave:
                    s.error_conexion = "Escribe la contraseña del panel."
                else:
                    abrir_sesion(ip.strip(), clave, False)
            if s.error_conexion:
                st.error(s.error_conexion)
                if s.diag_login:
                    with st.expander("Diagnóstico técnico del login"):
                        st.caption("Solo códigos y longitudes; no contiene tu contraseña.")
                        st.json(s.diag_login)
        else:
            ses = s.sesion
            tipo = ui.chip("simulación", "vi") if ses.simulado else ui.chip("en línea", "ok")
            st.markdown(tipo + ui.chip(ses.ip), unsafe_allow_html=True)
            nombres = list(MODOS)
            modo = st.radio("MODO DE OPERACIÓN", nombres, index=nombres.index(ses.modo.value),
                            format_func=str.upper)
            ses.guardian.modo = Modo(modo)
            st.caption(MODOS[modo])
            if s.error_conexion:
                st.error(s.error_conexion)
            if st.button("DESCONECTAR"):
                ses.router.desconectar()
                for clave_estado, valor in ESTADO_INICIAL.items():
                    s[clave_estado] = list(valor) if isinstance(valor, list) else dict(valor) if isinstance(valor, dict) else valor
                st.rerun()


# --------------------------------------------------------------------------- dibujar respuestas
def dibujar_respuesta(r):
    if r.medicion is not None:
        m, d = r.medicion, r.diagnostico
        g = m.gateway if m.tiene_gateway and m.gateway.conexion else None
        st.markdown(ui.panel("ENLACE", ui.medidores_red(
            m.internet.latencia, m.internet.perdida, m.internet.jitter, g.latencia if g else None)),
            unsafe_allow_html=True)
        fuente = "modelo de ML" if d.origen == "ml" else "reglas"
        if d.confianza is not None:
            fuente += f" · {d.confianza:.0%}"
        st.markdown(ui.diagnostico_card(d.mensaje, d.recomendacion, fuente, ui.nivel_de_problema(d.problema)),
                    unsafe_allow_html=True)
    elif r.intencion == "listar_dispositivos" and r.datos.get("dispositivos"):
        st.markdown(ui.panel("DISPOSITIVOS DETECTADOS", ui.tabla_dispositivos(r.datos["dispositivos"])),
                    unsafe_allow_html=True)
    elif r.intencion == "analizar_wifi" and r.datos.get("correcto"):
        st.bar_chart(r.datos["redes_por_canal"])
    elif r.intencion == "info_router" and r.datos:
        st.json(r.datos)


def dibujar_turno(t):
    with st.chat_message("user" if t.rol == "usuario" else "assistant"):
        if t.texto:
            st.markdown(t.texto)
        if t.respuesta is not None:
            dibujar_respuesta(t.respuesta)
        if t.clientes:
            st.markdown(ui.panel("CLIENTES DEL ROUTER", ui.tabla_dispositivos(t.clientes)), unsafe_allow_html=True)


# ------------------------------------------------------------------------------------ pestañas
def panel_confirmacion():
    s = st.session_state
    if not s.pendiente:
        return
    p = s.pendiente
    aviso = ""
    if p["accion"] == "cambiar_canal" and not s.sesion.simulado:
        aviso = ("<p>⚠ Si tu PC está por Wi-Fi perderás la conexión unos segundos. HERMES verificará la red "
                 "y revertirá el cambio si deja de responder.</p>")
    st.markdown(ui.panel("CONFIRMACIÓN REQUERIDA", f'<p class="dato">{ui.esc(p["descripcion"])}</p>{aviso}'),
                unsafe_allow_html=True)
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button("CONFIRMAR Y EJECUTAR", type="primary", key="confirmar_ok"):
        s.pendiente = None
        ejecutar_y_registrar(p["accion"], p["valor"], p["descripcion"], True)
        st.rerun()
    if c2.button("CANCELAR", key="confirmar_no"):
        s.pendiente = None
        s.historial.append(Turno("hermes", "Acción cancelada. No se modificó nada."))
        st.rerun()


def pestana_consola():
    s = st.session_state
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    if c1.button("DIAGNOSTICAR RED", key="rapido_red"):
        s["cola"] = "revisar mi red"
    if c2.button("DISPOSITIVOS", key="rapido_disp"):
        s["cola"] = "cuantos dispositivos hay en mi red"
    if c3.button("ANALIZAR WI-FI", key="rapido_wifi"):
        s["cola"] = "que canal wifi me conviene"
    if not s.historial:
        st.markdown(ui.panel("CONSOLA", "<p>Escribe abajo o usa un acceso rápido.</p>"), unsafe_allow_html=True)
    for turno in s.historial[-30:]:
        dibujar_turno(turno)


def pestana_dispositivos():
    s, ses = st.session_state, st.session_state.sesion
    c1, c2, _ = st.columns([1, 1, 2])
    if ses is not None and c1.button("ACTUALIZAR", key="act_clientes"):
        refrescar()
    if c2.button("ESCANEAR LA RED", key="escanear"):
        with st.spinner("Escaneando tu subred…"):
            try:
                s.escaneo = [asdict(d) for d in dispositivos.escanear()]
            except Exception as error:
                st.error(f"No se pudo escanear: {error}")
    if ses is None:
        st.markdown(ui.banner("Conecta el router (panel lateral) para bloquear o desbloquear dispositivos."),
                    unsafe_allow_html=True)
    else:
        st.markdown(f"##### {len(s.clientes)} DISPOSITIVOS EN EL ROUTER")
        for i, c in enumerate(s.clientes):
            col = st.columns([2.4, 3, 2, 1.6])
            nombre = c.get("nombre") or "—"
            col[0].markdown(f'<span class="dato">{ui.esc(nombre)}</span>', unsafe_allow_html=True)
            col[1].markdown(f'<span class="dato">{ui.esc(c.get("ip") or "?")} · {ui.esc(c["mac"])}</span>',
                            unsafe_allow_html=True)
            if c["mac"] in ses.protegidos:
                col[2].markdown(ui.chip("protegido", "vi"), unsafe_allow_html=True)
            elif c["bloqueado"]:
                col[2].markdown(ui.chip("bloqueado", "bad"), unsafe_allow_html=True)
                if col[3].button("DESBLOQUEAR", key=f"des_{i}"):
                    solicitar("desbloquear_cliente", c["mac"], f"Desbloquear a {nombre} ({c['mac']})")
                    st.rerun()
            else:
                col[2].markdown(ui.chip("activo", "ok"), unsafe_allow_html=True)
                if col[3].button("BLOQUEAR", key=f"blo_{i}"):
                    solicitar("bloquear_cliente", c["mac"], f"Bloquear a {nombre} ({c['mac']})")
                    st.rerun()
    if s.escaneo:
        st.markdown(ui.panel("ESCANEO DE LA SUBRED (ARP)", ui.tabla_dispositivos(s.escaneo)),
                    unsafe_allow_html=True)


def pestana_router():
    s, ses = st.session_state, st.session_state.sesion
    if ses is None:
        st.markdown(ui.banner("Sin enlace con el router."), unsafe_allow_html=True)
        return
    info, wifi = s.info, s.wifi
    cuerpo = (f'<p class="dato">{ui.esc(info.get("fabricante", "?"))} {ui.esc(info.get("modelo", ""))} · '
              f'IP {ui.esc(info.get("ip_lan") or ses.ip)}</p>'
              f'<p class="dato">Wi-Fi: {ui.esc(wifi.get("ssid") or "?")} · canal '
              f'{"AUTOMÁTICO" if wifi.get("canal") == 0 else ui.esc(str(wifi.get("canal")))}</p>')
    capacidades = "".join(ui.chip(k.replace("_", " "), "ok" if v == "confirmada" else "warn")
                          for k, v in ses.router.obtener_capacidades().items())
    st.markdown(ui.panel("ROUTER", cuerpo + f"<p>{capacidades}</p>"), unsafe_allow_html=True)

    opciones = [0] + [c for c in s.canales if c != 0]
    actual = wifi.get("canal") if wifi.get("canal") in opciones else 0
    canal = st.selectbox("CANAL WI-FI", opciones, index=opciones.index(actual),
                         format_func=lambda c: "AUTOMÁTICO" if c == 0 else str(c))
    if st.button("APLICAR CANAL", key="aplicar_canal"):
        nombre = "automático" if canal == 0 else str(canal)
        solicitar("cambiar_canal", canal, f"Cambiar el canal Wi-Fi a {nombre}")
        st.rerun()
    if s.registro:
        filas = "".join(f"<tr><td>{ui.esc(h)}</td><td>{ui.esc(d)}</td><td>{ui.esc(r)}</td></tr>"
                        for h, d, r in s.registro[:12])
        st.markdown(ui.panel("REGISTRO DE ACCIONES", '<table class="tabla"><thead><tr><th>HORA</th>'
                             f'<th>ACCIÓN</th><th>RESULTADO</th></tr></thead><tbody>{filas}</tbody></table>'),
                    unsafe_allow_html=True)


# ------------------------------------------------------------------------------------ principal
iniciar()
barra_lateral()
ses = st.session_state.sesion
estado = "offline" if ses is None else "simulacion" if ses.simulado else "conectado"
st.markdown(ui.hero(estado), unsafe_allow_html=True)
if ses is not None and ses.simulado:
    st.markdown(ui.banner("MODO SIMULACIÓN · router de mentira, sin riesgo."), unsafe_allow_html=True)
panel_confirmacion()

tab_consola, tab_disp, tab_router = st.tabs(["CONSOLA", "DISPOSITIVOS", "ROUTER"])
with tab_consola:
    pestana_consola()
with tab_disp:
    pestana_dispositivos()
with tab_router:
    pestana_router()

entrada = st.chat_input("Habla con HERMES…  «revisa mi red» · «bloquea el celular» · «cambia el canal a 6»")
texto = entrada or st.session_state.pop("cola", None)
if texto:
    procesar(texto)
    st.rerun()
