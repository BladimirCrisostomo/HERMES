# HERMES

### Sistema Inteligente de Administración y Diagnóstico de Redes

Proyecto de Inteligencia Artificial (metodología ABP). El usuario describe un problema de red en lenguaje natural, HERMES mide la red, clasifica el problema con Machine Learning y responde con un diagnóstico y recomendaciones.

> *"Mi Internet está muy lento y algunas páginas tardan demasiado en cargar."*

## Qué hace hoy

| Función | Cómo funciona |
|---|---|
| Entender la consulta | Palabras clave (sin acentos, palabras completas) + clasificador TF-IDF/regresión logística para frases nuevas |
| Medir la red | `ping` a Internet **y** al router → latencia, jitter y pérdida; funciona en Windows, Linux y macOS |
| Diagnosticar | Árbol de decisión (scikit-learn) con 5 variables; si duda o falta información usa reglas de respaldo |
| Distinguir la causa | Compara router vs. Internet: separa "falla tu Wi-Fi/router" de "falla el proveedor" |
| Analizar Wi-Fi | Escanea redes cercanas y sugiere el canal con menos interferencia (Windows y Linux) |
| Contar dispositivos | "¿Cuántos usuarios hay en mi red?" → lista IP, MAC, fabricante y nombre, **sin contraseña** |
| Conocer el router | Detecta puertos y portada web **sin iniciar sesión**, marcando qué capacidades están confirmadas |
| Administrar el router | Bloquear, limitar velocidad, cambiar canal y reiniciar, con modos sugerir/confirmar/automático, protecciones y reversión (ver abajo) |
| Interfaces | Consola (`app.py`) y **web estilo HUD** (`streamlit_app.py`): conecta el router con su contraseña, órdenes en lenguaje natural («bloquea el celular», «cambia el canal a 6»), modos sugerir/confirmar/automático y confirmación visual |

## Interfaz web (Streamlit)

```bash
streamlit run streamlit_app.py
```

- **Panel lateral:** IP del router y contraseña del panel (con la que entras a `mwlogin.net`; este router no usa usuario). La contraseña no se muestra, no se guarda y el formulario se vacía al enviarlo. Hay un límite de 3 intentos seguidos (luego espera 30 s) para no golpear el login del router. **DEMO** abre un router simulado, ideal para presentar sin riesgo.
- **Consola:** escribe o usa los accesos rápidos. Órdenes de ejemplo: «bloquea el celular», «desbloquea la tv», «cambia el canal a 6», «pon el canal en automático», «cuántos dispositivos hay». HERMES no bloquea «a todos», pide aclaración si el nombre es ambiguo y nunca ejecuta sin respetar el modo elegido.
- **Dispositivos / Router:** botones para bloquear, desbloquear y cambiar canal; registro de acciones; capacidades confirmadas del router.
- Si el login falla, el panel muestra un **diagnóstico técnico** (solo códigos y longitudes, sin contraseña) útil para depurar.
- El panel solo escucha en `127.0.0.1`: otra persona de tu red no puede abrirlo para administrar tu router.

## Instalación y uso

```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt

python app.py                  # consola
streamlit run streamlit_app.py # interfaz web
```

La primera vez que se usa el diagnóstico, HERMES entrena el modelo solo (menos de 1 s). Para entrenarlo manualmente y ver sus métricas:

```bash
python -m scripts.entrenar
```

## Estructura

```text
hermes/
├── app.py                    # interfaz de consola
├── streamlit_app.py          # interfaz web (estilo HUD)
├── .streamlit/config.toml    # tema oscuro; el panel solo escucha en 127.0.0.1
├── data/
│   ├── dataset.csv           # dataset sintético de entrenamiento (generado)
│   ├── dataset_inicial.csv   # primer dataset de 20 filas (histórico)
│   ├── intenciones.csv       # frases de ejemplo para el clasificador de intenciones
│   └── mediciones_reales.csv # tus mediciones reales (opcional, se crea solo)
├── models/                   # modelos entrenados (.joblib, se regeneran)
├── src/
│   ├── motor.py              # orquesta: consulta -> mediciones -> diagnóstico
│   ├── asistente.py          # órdenes en lenguaje natural y sesión con el router (sin Streamlit)
│   ├── ui_tema.py            # tema HUD (CSS) y componentes HTML, todo con texto escapado
│   ├── nlp.py                # identificación de intención
│   ├── network.py            # ping multiplataforma (latencia, jitter, pérdida)
│   ├── discovery.py          # IP local y gateway
│   ├── diagnostico.py        # ML + reglas de respaldo + recomendaciones
│   ├── machine_learning.py   # entrenamiento, evaluación y predicción
│   ├── dispositivos.py       # descubrimiento de dispositivos de la LAN
│   ├── politicas.py          # GuardianRouter: modos, protecciones, reversión
│   ├── credenciales.py       # usuario/contraseña del router (nunca en logs)
│   ├── seguridad.py          # validación de entradas y filtro de secretos
│   ├── config.py             # rutas, parámetros y logging
│   └── router/               # subsistema del router (solo lectura por defecto)
├── scripts/
│   ├── generar_dataset.py    # genera data/dataset.csv
│   ├── entrenar.py           # entrena y muestra métricas
│   ├── registrar_medicion.py # agrega una medición real etiquetada
│   ├── analizar_router.py    # exploración manual del router
│   ├── demo_simulacion.py    # demostración segura con un router simulado
│   ├── probar_mw306r.py      # primera prueba controlada contra el MW306R real
│   └── limpiar_har.py        # limpia capturas HAR del panel (borra claves, PIN, sesiones)
├── tests/                    # pruebas automáticas
├── requirements.txt
└── .env.example
```

## Pruebas

```bash
python -m unittest discover -s tests -t .   # o: pytest
```

Las pruebas no necesitan red ni router: usan salidas de ejemplo de `ping`, `route print`, `netsh`, etc.

## Sobre el modelo de ML (importante para la presentación)

- El dataset base es **sintético**: se genera con distribuciones que se solapan entre clases (`scripts/generar_dataset.py`), así el modelo aprende fronteras estadísticas y no copia umbrales exactos.
- La precisión que reporta `scripts.entrenar` (~95%) mide qué tan bien reproduce **ese** dataset, no cómo se comportará en cualquier red del mundo real.
- Para adaptarlo a tu red: provoca situaciones reales (alejarte del router, hacer una descarga grande, desconectar el cable) y registra cada una con `python -m scripts.registrar_medicion`. Con 50–100 mediciones reales, reentrena con `python -m scripts.entrenar`.
- Se usa un árbol de decisión porque es **explicable**: `scripts.entrenar` imprime las reglas que aprendió.
- Clases: `estable`, `latencia_moderada`, `latencia_alta`, `perdida_paquetes`, `inestable`, `red_local_degradada`. Las situaciones sin conexión (`sin_internet`, `sin_red_local`) se resuelven con reglas, porque sin respuesta no hay datos que clasificar.

## Administración del router

HERMES puede modificar un router **solo si el usuario aporta su propio usuario y contraseña de administrador** y existe un adaptador para ese modelo. Todo cambio pasa por `GuardianRouter`:

| Modo | Comportamiento |
|---|---|
| `sugerir` | Describe lo que haría; no ejecuta nada |
| `confirmar` | Pregunta al usuario antes de cada cambio |
| `automatico` | Ejecuta sin preguntar **solo** cambiar canal y limitar velocidad. Bloquear y reiniciar siempre piden confirmación |

Protecciones fijas: nunca bloquea ni limita **este equipo** ni **el propio router**; no bloquea a la mitad o más de la red; máximo 4 cambios por hora; guarda el estado previo, comprueba que la red sigue funcionando tras el cambio y, si no, **lo revierte solo**; cada acción queda en `logs/hermes.log`. Cambiar el canal puede desconectar un instante a quien esté por Wi-Fi: la primera prueba real conviene hacerla **por cable**.

**Adaptadores.** HERMES identifica el router por su portada/puertos y elige el adaptador registrado en `src/router/registro.py`. Hoy existen: `simulado` (pruebas y demostraciones), `mercusys_mw306r` (**en construcción**, ver abajo) y la plantilla `adapters/plantilla.py` para crear otros.

**Mercusys MW306R (V1).** El protocolo del panel se dedujo de capturas reales (`scripts/limpiar_har.py` las limpia antes de compartirlas). Implementado y probado con un router simulado: inicio de sesión, listar clientes, leer/cambiar el canal (con verificación y reversión) y bloquear/desbloquear. Pendientes: el módulo QoS (límite por dispositivo, que el menú del panel sí tiene) y el reinicio. **Nada se ha ejecutado todavía contra el router real:** la primera prueba se hace con `python -m scripts.probar_mw306r 192.168.1.1` (solo lectura por defecto; conecta la PC por cable). Ojo: en este modelo el `id` de cada petición es la contraseña cifrada de forma reversible y viaja por HTTP; úsalo solo en una red propia y no reutilices esa contraseña en otros sitios.

```bash
python -m scripts.demo_simulacion   # ver los modos, protecciones y reversión sin tocar nada real
```

## Seguridad

- Los comandos del sistema se ejecutan **sin shell** y con tiempo límite; el host del ping se valida (no puede ser una opción como `-f`).
- Las consultas del usuario se limpian (caracteres de control, longitud máxima).
- HERMES solo sondea **IPs privadas** (tu red local), nunca equipos de Internet.
- El subsistema del router está dividido: `RouterReader` (solo lectura, lo que usa el diagnóstico) y `RouterController` (puede modificar). Las acciones que modifican pasan por `RouterManager.ejecutar_accion()`: validan el valor, exigen que la capacidad esté **confirmada**, piden confirmación al usuario y quedan registradas en `logs/hermes.log`.
- La contraseña del router se pide con `getpass` (no se muestra), vive solo en memoria, **se oculta de los logs** y solo se guarda en el llavero del sistema si el usuario lo decide (`keyring`, opcional). Si el router solo ofrece HTTP, HERMES avisa de que las credenciales viajan sin cifrar por la red local.
- No hay credenciales en el código; los parámetros se leen del entorno (ver `.env.example`).
- Usa HERMES únicamente en redes propias o con autorización.

## Limitaciones conocidas

- El adaptador del MW306R está probado solo contra un router simulado; falta validarlo en el equipo real, y faltan QoS y reinicio.
- El listado de dispositivos cuenta dispositivos, no personas; los móviles con MAC privada pueden verse como otro dispositivo y bloquearlos por MAC puede no ser permanente. Para ver el fabricante de más equipos, descarga `oui.csv` del IEEE y guárdalo en `data/`.
- Se asume una subred /24 para el escaneo.
- El escaneo Wi-Fi solo cubre 2.4 GHz y funciona en Windows y Linux (macOS no soportado).
- En Windows 11 el escaneo Wi-Fi puede requerir el permiso de ubicación.
- El diagnóstico con ML necesita poder medir el router (gateway); si no se detecta, se usan reglas.

## Equipo

| Integrante | Área principal | Responsabilidades |
|---|---|---|
| jose | IA + Backend | Machine Learning, NLP, lógica de diagnóstico, módulos principales |
| V | Redes + Interfaz | Datos de red, pruebas de conectividad, interfaz, integración y pruebas |

Ambos participan en integración, pruebas, documentación, revisión de código, seguridad, Git/GitHub y presentación.
fg
## Propósito académico

HERMES aplica IA y aprendizaje automático a un problema real de administración de redes, integrando Python, procesamiento de datos, Machine Learning, NLP, redes, interfaces, pruebas y control de versiones.
