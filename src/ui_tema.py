"""Tema visual futurista (estilo HUD) y componentes HTML para la interfaz de HERMES.

TODO texto que provenga de la red o del usuario (nombres de dispositivos, SSID, consultas)
se escapa con `esc()` antes de insertarlo en HTML: un dispositivo llamado
"<script>..." no debe poder ejecutar nada en el navegador.
"""
import html

esc = html.escape

ESTADOS = {
    "offline": "SIN ENLACE CON EL ROUTER",
    "conectado": "ENLACE ESTABLE",
    "simulacion": "MODO SIMULACIÓN",
    "alerta": "ALERTA · REVISA EL ENLACE",
}

# Estilo "Tron": negro y blanco, líneas finas con brillo. Los estados NO usan color:
# bien = línea blanca, aviso = línea discontinua o gris, crítico = bloque invertido (blanco).
TEMA_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@400;500;600&family=Share+Tech+Mono&display=swap');
:root{--w:#fff;--g1:#cfcfcf;--g2:#8a8a8a;--g3:#444;--line:rgba(255,255,255,.55)}
.stApp{background:#000;color:#f2f2f2;font-family:'Rajdhani','Segoe UI',sans-serif;font-size:1.05rem}
.stApp::before{content:"";position:fixed;left:-60%;right:-60%;bottom:0;height:48vh;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(255,255,255,.16) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.16) 1px,transparent 1px);
  background-size:64px 64px;transform:perspective(380px) rotateX(64deg);transform-origin:50% 100%;
  -webkit-mask-image:linear-gradient(to top,rgba(0,0,0,.75),transparent 88%);mask-image:linear-gradient(to top,rgba(0,0,0,.75),transparent 88%)}
::selection{background:#fff;color:#000}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
.block-container{padding-top:1.4rem;max-width:1150px}
h1,h2,h3,h4,h5{font-family:'Orbitron',sans-serif!important;letter-spacing:.2em;text-transform:uppercase;color:#fff!important;font-weight:500!important}
section[data-testid="stSidebar"]{background:#000;border-right:1px solid var(--line);box-shadow:0 0 22px rgba(255,255,255,.08)}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:#f2f2f2}
a{color:#fff}

/* botones: contorno blanco; al pasar el ratón se invierten */
.stButton>button,.stFormSubmitButton>button{background:transparent;color:#fff;border:1px solid #fff;border-radius:0;
  font-family:'Orbitron',sans-serif;letter-spacing:.18em;font-size:.66rem;text-transform:uppercase;transition:all .15s}
.stButton>button:hover,.stFormSubmitButton>button:hover{background:#fff;color:#000;box-shadow:0 0 18px rgba(255,255,255,.7)}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"],
button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-primaryFormSubmit"]{background:#fff;color:#000}
.stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primary"]:hover{background:#000;color:#fff}

/* campos */
.stTextInput input,.stNumberInput input,.stTextArea textarea,
.stSelectbox div[data-baseweb="select"]>div,[data-testid="stChatInput"] textarea{
  background:#000!important;color:#fff!important;border:1px solid var(--line)!important;border-radius:0!important;
  font-family:'Share Tech Mono',monospace!important}
.stTextInput input:focus,[data-testid="stChatInput"] textarea:focus{border-color:#fff!important;box-shadow:0 0 14px rgba(255,255,255,.45)!important}
[data-testid="stChatInput"]{background:#000;border:1px solid #fff;border-radius:0;box-shadow:0 0 18px rgba(255,255,255,.15)}

/* pestañas */
button[data-baseweb="tab"]{font-family:'Orbitron',sans-serif;letter-spacing:.2em;font-size:.7rem;color:var(--g2)}
button[data-baseweb="tab"][aria-selected="true"]{color:#fff}
[data-baseweb="tab-highlight"]{background:#fff!important;box-shadow:0 0 12px #fff}
[data-baseweb="tab-border"]{background:rgba(255,255,255,.2)!important}

/* chat y desplegables */
[data-testid="stChatMessage"]{background:rgba(0,0,0,.78);border:1px solid rgba(255,255,255,.22);border-left:3px solid #fff;
  border-radius:0;padding:.7rem 1rem}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){border-left:3px dashed var(--g2)}
[data-testid="stExpander"]{border:1px solid rgba(255,255,255,.3);border-radius:0;background:#000}

/* cabecera: disco de identidad + horizonte */
.hero{display:flex;align-items:center;gap:28px;padding:6px 4px 20px;margin-bottom:18px;border-bottom:1px solid #fff;
  box-shadow:0 16px 26px -20px rgba(255,255,255,.75)}
.disco{position:relative;width:92px;height:92px;flex:0 0 92px}
.d1,.d2,.d3{position:absolute;border-radius:50%}
.d1{inset:0;border:3px solid #fff;border-right-color:transparent;box-shadow:0 0 16px rgba(255,255,255,.75);
  animation:girar 14s linear infinite}
.d2{inset:15px;border:1px solid rgba(255,255,255,.75)}
.d3{inset:40px;background:#fff;box-shadow:0 0 14px #fff}
.estado-offline .d1{border-style:dashed;border-color:var(--g2);border-right-color:transparent;box-shadow:none;animation:none}
.estado-offline .d3{background:var(--g3);box-shadow:none}
.estado-simulacion .d1{border-style:double;border-width:6px;border-right-color:transparent}
.estado-alerta .d1{background:#fff;border-right-color:#fff;animation:none}
.estado-alerta .d2{border-color:#000}.estado-alerta .d3{background:#000;box-shadow:none}
.kicker{font-family:'Share Tech Mono',monospace;font-size:.72rem;letter-spacing:.4em;color:var(--g2)}
.titulo{font-family:'Orbitron',sans-serif;font-weight:700;font-size:2.7rem;letter-spacing:.45em;line-height:1.1;color:#fff;
  text-shadow:0 0 20px rgba(255,255,255,.6)}
.sub{font-family:'Share Tech Mono',monospace;font-size:.82rem;letter-spacing:.24em;color:var(--g1);margin-top:4px}

/* paneles */
.hud{background:rgba(0,0,0,.8);border:1px solid var(--line);padding:14px 18px;margin:6px 0 14px;box-shadow:0 0 16px rgba(255,255,255,.05)}
.hud-t{font-family:'Orbitron',sans-serif;font-size:.66rem;letter-spacing:.28em;color:#fff;margin-bottom:10px;display:flex;align-items:center;gap:10px}
.hud-t::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(255,255,255,.55),transparent)}
.hud p{margin:.25rem 0}
.dato{font-family:'Share Tech Mono',monospace;color:#fff}

/* medidores */
.gauges{display:flex;flex-wrap:wrap;gap:30px;justify-content:center;padding:6px 0 4px}
.gauge{display:flex;flex-direction:column;align-items:center;gap:8px}
.ring-g{--gc:#fff;width:116px;height:116px;border-radius:50%;display:grid;place-items:center;
  background:conic-gradient(var(--gc) calc(var(--p)*1%),rgba(255,255,255,.13) 0);filter:drop-shadow(0 0 6px rgba(255,255,255,.55))}
.nivel-warn .ring-g{--gc:#9d9d9d;filter:none} .nivel-off .ring-g{--gc:#444;filter:none}
.in-g{width:96px;height:96px;border-radius:50%;background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center}
.nivel-bad .in-g{background:#fff}
.val-g{font-family:'Orbitron',sans-serif;font-weight:700;font-size:1.35rem;color:#fff}
.u-g{font-family:'Share Tech Mono',monospace;font-size:.7rem;color:var(--g2);letter-spacing:.14em}
.nivel-bad .val-g,.nivel-bad .u-g{color:#000}
.lab-g{font-family:'Orbitron',sans-serif;font-size:.6rem;letter-spacing:.26em;color:var(--g1)}
.nivel-warn .lab-g::before{content:"△ "} .nivel-bad .lab-g::before{content:"▲ "}

/* etiquetas y avisos */
.chip{display:inline-block;font-family:'Share Tech Mono',monospace;font-size:.72rem;letter-spacing:.12em;padding:1px 9px;
  border:1px solid #fff;color:#fff;margin-right:6px;text-transform:uppercase}
.chip.warn{border-style:dashed} .chip.bad{background:#fff;color:#000} .chip.vi{border-color:var(--g2);color:var(--g1)}
.banner{border:1px dashed var(--line);background:rgba(255,255,255,.04);color:var(--g1);padding:8px 14px;margin-bottom:12px;
  font-family:'Share Tech Mono',monospace;font-size:.82rem;letter-spacing:.1em}
.banner.warn{border-style:solid} .banner.bad{background:#fff;color:#000}

/* tabla */
.tabla{width:100%;border-collapse:collapse;font-family:'Share Tech Mono',monospace;font-size:.86rem}
.tabla th{font-family:'Orbitron',sans-serif;font-size:.6rem;letter-spacing:.22em;color:var(--g2);text-align:left;padding:6px 10px;border-bottom:1px solid #fff}
.tabla td{padding:7px 10px;border-bottom:1px solid rgba(255,255,255,.12);color:#fff}
.tabla tr:hover td{background:rgba(255,255,255,.07)}

@keyframes girar{to{transform:rotate(360deg)}}
@media (max-width:760px){.hero{flex-direction:column;text-align:center}.titulo{font-size:1.9rem}}
@media (prefers-reduced-motion:reduce){.d1{animation:none}}
</style>
"""


def hero(estado="offline", subtitulo=None):
    texto = subtitulo or ESTADOS.get(estado, ESTADOS["offline"])
    return (
        f'<div class="hero estado-{esc(estado)}"><div class="disco">'
        '<div class="d1"></div><div class="d2"></div><div class="d3"></div></div><div>'
        '<div class="kicker">ADMINISTRACIÓN DE REDES</div><div class="titulo">HERMES</div>'
        f'<div class="sub">{esc(texto)}</div></div></div>'
    )


def panel(titulo, cuerpo_html):
    """`cuerpo_html` debe venir ya escapado por quien lo construye."""
    return f'<div class="hud"><div class="hud-t">{esc(titulo)}</div>{cuerpo_html}</div>'


def chip(texto, nivel=""):
    return f'<span class="chip {esc(nivel)}">{esc(str(texto))}</span>'


def banner(texto, nivel=""):
    return f'<div class="banner {esc(nivel)}">{esc(texto)}</div>'


# --- medidores --------------------------------------------------------------------
def nivel_latencia(ms):
    return "off" if ms is None else "ok" if ms < 50 else "warn" if ms < 100 else "bad"


def nivel_perdida(pct):
    return "off" if pct is None else "ok" if pct <= 1 else "warn" if pct <= 10 else "bad"


def nivel_jitter(ms):
    return "off" if ms is None else "ok" if ms < 15 else "warn" if ms < 30 else "bad"


def medidor(etiqueta, valor, unidad, nivel, escala):
    """Anillo tipo HUD. `escala` = valor que llena el anillo por completo."""
    if valor is None:
        pct, texto = 0, "—"
    else:
        pct = 0 if valor == 0 else max(4, min(100, round(valor / escala * 100)))
        texto = f"{valor:g}"
    return (
        f'<div class="gauge nivel-{esc(nivel)}"><div class="ring-g" style="--p:{pct}"><div class="in-g">'
        f'<span class="val-g">{esc(texto)}</span><span class="u-g">{esc(unidad)}</span></div></div>'
        f'<div class="lab-g">{esc(etiqueta)}</div></div>'
    )


def medidores_red(latencia, perdida, jitter, lat_gateway=None):
    piezas = [
        medidor("LATENCIA", latencia, "ms", nivel_latencia(latencia), 200),
        medidor("PÉRDIDA", perdida, "%", nivel_perdida(perdida), 30),
        medidor("JITTER", jitter, "ms", nivel_jitter(jitter), 60),
    ]
    if lat_gateway is not None:
        piezas.append(medidor("ROUTER", lat_gateway, "ms", nivel_latencia(lat_gateway * 2), 100))
    return '<div class="gauges">' + "".join(piezas) + "</div>"


def diagnostico_card(mensaje, recomendacion, fuente, nivel=""):
    cuerpo = (f'<p class="dato">{esc(mensaje)}</p><p>▸ {esc(recomendacion)}</p>'
              f'<p>{chip(fuente, nivel or "vi")}</p>')
    return panel("DIAGNÓSTICO", cuerpo)


def nivel_de_problema(problema):
    if problema == "estable":
        return "ok"
    if problema in ("latencia_moderada", "inestable"):
        return "warn"
    return "bad"


# --- tabla de dispositivos -----------------------------------------------------------
def tabla_dispositivos(clientes):
    filas = []
    for c in clientes:
        etiquetas = []
        if c.get("es_este_equipo"):
            etiquetas.append(chip("este equipo", "vi"))
        if c.get("es_gateway"):
            etiquetas.append(chip("router", "vi"))
        if c.get("bloqueado"):
            etiquetas.append(chip("bloqueado", "bad"))
        if c.get("mac_aleatoria"):
            etiquetas.append(chip("MAC privada", "warn"))
        nombre = c.get("nombre") or c.get("fabricante") or "—"
        filas.append(
            f'<tr><td>{esc(c.get("ip") or "?")}</td><td>{esc(c.get("mac") or "?")}</td>'
            f'<td>{esc(nombre)}</td><td>{"".join(etiquetas) or chip("activo", "ok")}</td></tr>')
    return ('<table class="tabla"><thead><tr><th>IP</th><th>MAC</th><th>DISPOSITIVO</th><th>ESTADO</th></tr></thead>'
            f'<tbody>{"".join(filas)}</tbody></table>')
