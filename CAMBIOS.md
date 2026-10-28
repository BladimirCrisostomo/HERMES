# Qué cambió respecto a la versión anterior (y por qué)

## Corregido (bugs reales)
- `recomendar()` fallaba con `TypeError` si el ping no devolvía datos -> ahora todo pasa por `diagnosticar()`, que maneja valores ausentes.
- `network.py` solo funcionaba en Windows en español -> ahora cuenta respuestas individuales del ping (independiente del idioma y del sistema).
- `discovery.obtener_gateway()` dependía de `ipconfig` en español y podía devolver basura con IPv6 -> usa `route print` (Windows), `/proc/net/route` / `ip route` (Linux) y `route get` (macOS).
- Imports que solo funcionaban según la carpeta desde donde ejecutabas (`from detector import ...`) -> imports relativos de paquete.
- `machine_learning.py` leía `data/dataset.csv` con ruta relativa -> rutas absolutas desde `src/config.py`.
- El árbol cambiaba entre ejecuciones (sin `random_state`) y memorizaba los datos -> `random_state=42`, `max_depth=6`, `min_samples_leaf=5`.

## Mejorado
- El modelo de ML **ahora sí se usa** en `app.py`; se evalúa (validación cruzada, matriz de confusión) y se guarda en `models/`.
- Nueva variable clave: latencia/pérdida hacia el **router** -> separa problema local de problema del proveedor.
- NLP: normaliza acentos y mayúsculas, usa palabras completas (`lag` ya no coincide con `plaga`) y agrega un clasificador entrenado para frases nuevas.
- `web_info.py` y `generic_http.py` duplicaban el mismo GET -> un solo `http_client.py` (con tamaño máximo de respuesta). Ya no se devuelve el HTML completo.
- `RouterInterface` dividida en `RouterReader` / `RouterController`; las acciones que modifican exigen capacidad confirmada + confirmación del usuario + registro.
- Detección de puertos en paralelo (hasta 3 s -> ~1 s).
- Analizador Wi-Fi: considera el solapamiento de canales vecinos y soporta Linux; las redes de 5 GHz ya no distorsionan el conteo.
- `app.py`: 3 bloques repetidos -> 1 flujo; bucle de consultas; sin comentarios informales.

## Reorganizado
- Los 14 `test_*.py` de `src/` eran scripts manuales contra tu router (IP fija `192.168.100.1`). Se reemplazaron por `tests/` (56 pruebas automáticas sin red) y `scripts/analizar_router.py`.
- `RouterCapabilities` (clase sin uso) -> constantes en `capabilities.py`.
- `.gitignore` sin duplicados; se agregaron `requirements.txt`, `.env.example`, `models/`, `tests/` y logging (todo lo que el README prometía).

## Nuevo: administración multi-router (segunda ronda)
- `dispositivos.py`: "¿cuántos usuarios hay?" sin contraseña (sondeo ARP de tu subred, fabricante por MAC, detección de MAC privada).
- `router/registro.py`: HERMES identifica el router y elige el adaptador; `adapters/simulado.py` permite probar todo sin riesgo; `adapters/plantilla.py` guía el primer adaptador real.
- `politicas.py`: `GuardianRouter` con modos sugerir/confirmar/automático, objetivos protegidos, límite de cambios por hora, verificación de red y **reversión automática**.
- `credenciales.py`: contraseña con `getpass`, oculta en logs, llavero opcional, aviso si el router usa solo HTTP.
- Interfaz del router ampliada: `limitar_cliente`, `quitar_limite`, `reiniciar` (reemplaza `configurar_qos`).
- Nueva intención de lenguaje natural `listar_dispositivos`; el modelo de intenciones se reentrena solo si cambian las frases.
- 96 pruebas automáticas (antes 56).

## Nuevo: adaptador del Mercusys MW306R (tercera ronda)
- `adapters/mercusys_mw306r.py`: protocolo del panel (`/?code=N&asyn=M&id=...`) deducido de capturas reales. Lectura de clientes, canal, cambio de canal con verificación, bloqueo (armado y saneado del comando). Probado con un router simulado (21 pruebas nuevas, 117 en total).
- `scripts/limpiar_har.py` corregido: ahora oculta también claves en formato "clave valor" (`cPskSecret`, `cUsrPIN`, `authKey`), PIN y el `id` de sesión de la URL, y tiene `--sin-ocultar` solo para capturar el login con una contraseña temporal.
- El canal `0` (automático) ahora es válido, necesario para revertir un cambio de canal a como estaba.
- Seguridad: las claves que el router devuelve se registran como secretos y se ocultan de los logs; el bloqueo no activa por su cuenta el control de acceso del router.

## Cuarta ronda: login y desbloqueo del MW306R
- Login implementado: el `id` de cada petición es la contraseña cifrada (`su.encrypt` del panel, portado a Python y verificado con cálculos a mano). Los parámetros los entrega el router en un 401 sin credenciales. Tras entrar se comprueba que el modelo sea MW306R; con otro modelo se niega a operar.
- Desbloqueo (`advanced bm rule -del list:black mac:...`) y verificación de bloqueo/desbloqueo leyendo la lista negra. `bloquear_cliente` pasa a *confirmada* (visto en capturas); sigue exigiendo confirmación incluso en modo automático.
- El menú del panel incluye `qos`: `limitar_cliente` queda *no verificada* en espera de captura (antes la di por no disponible).
- `scripts/probar_mw306r.py`: primera prueba real, solo lectura por defecto.
- 132 pruebas automáticas.

## Quinta ronda: interfaz HUD y control desde Streamlit
- `streamlit_app.py` rehecho: estética futurista (núcleo animado que cambia de color según el estado, medidores circulares, paneles con esquinas, cuadrícula de fondo), conexión al router con contraseña, modos de operación, confirmación visual y registro de acciones.
- `src/asistente.py`: órdenes en lenguaje natural («bloquea el poco», «desbloquea la 192.168.1.104», «cambia el canal a 6»), límite de intentos de login y sesión con el router, todo probado sin navegador.
- `src/ui_tema.py`: todo texto que viene de la red (nombres de dispositivos, SSID) se **escapa** antes de dibujarse: un dispositivo llamado `<script>` se ve como texto y no se ejecuta.
- `.streamlit/config.toml`: tema oscuro y `address = "127.0.0.1"` (solo tu PC abre el panel).
- Login del MW306R: ya no exige que el cuerpo sea exactamente `00000`; la prueba real es poder leer un dato protegido. Nuevo `diagnosticar_login()` que reporta cada paso sin secretos.
- 169 pruebas automáticas (incluye un Streamlit simulado que ejecuta la app completa).

## Sexta ronda: detección del router
- Nueva huella: `POST /?code=7&asyn=1` sin credenciales responde 401 con parámetros de login solo en este tipo de panel. Identifica el router sin depender de que el HTML diga «Mercusys». Un módem de proveedor no la cumple.
- Botón **BUSCAR MI ROUTER** (`registro.buscar_routers`): sondea en paralelo las IPs comunes y marca compatibles / no compatibles.
- Mensaje claro cuando el equipo no es compatible: indica qué servidor/título detectó, aclara que el módem del proveedor no se administra y qué hacer.
- 178 pruebas automáticas.

## Séptima ronda: login corregido y rediseño Tron
- **Login del MW306R:** ahora replica el flujo exacto del panel: pide los parámetros con `code=2` (getLoginParams) justo antes de cifrar la contraseña (antes usaba `code=7`, que el panel solo usa al arrancar). Se verificó el cifrado, el mapeo de `authInfo` y la ausencia de cookies contra el JavaScript del panel capturado.
- **Un solo intento de login por clic.** Antes, tras un fallo se hacía un segundo intento solo para «diagnosticar»; ahora los pasos (códigos HTTP y longitudes, sin secretos) se registran durante el intento real y se muestran en el panel. Menos riesgo de bloqueo temporal del router.
- **Interfaz más simple, en blanco y negro (estilo Tron):** disco de identidad, horizonte, cuadrícula en perspectiva; estados por forma (línea / discontinua / bloque invertido) y no por color; textos más cortos.
- **Corrección clave del login (octava ronda):** el diagnóstico de un router real mostró que el cuerpo del 401 trae 6 líneas con largos `[5, 5, 5, 32, 255, 5]`: la CLAVE es la línea de 32 caracteres y la TABLA la de 255. La primera versión tomaba las líneas 3 y 4 (de 5 y 32) y por eso el login fallaba con cualquier contraseña. Ahora la tabla es la línea más larga y la clave la anterior, sin depender de si hay una línea de código al inicio.
- 183 pruebas automáticas.

## Pendiente (siguientes pasos sugeridos)
1. Registrar 50–100 mediciones reales con `scripts/registrar_medicion.py` y reentrenar.
2. Probar en tu Windows: `python app.py`, `python -m scripts.analizar_router` y `streamlit run streamlit_app.py` (no pude probar Windows ni Streamlit en mi entorno).
3. Probar el adaptador del MW306R en el equipo real (`scripts/probar_mw306r.py`), por cable y con un solo dispositivo de prueba. Después capturar QoS (límite por dispositivo) y reinicio.
4. Frases en lenguaje natural para actuar ("bloquea a X", "limita a 5 Mbps") conectadas al `GuardianRouter`.
