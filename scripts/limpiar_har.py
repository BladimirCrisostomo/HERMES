"""Limpia una captura HAR del panel de tu router para poder compartirla sin riesgo.

Qué hace:
  - Quita imágenes, estilos y fuentes (lo que no sirve para analizar el panel).
  - Borra contraseñas, claves Wi-Fi, PIN, cookies, tokens, ids de sesión y cabeceras de autorización.
  - Recorta las respuestas largas.
  - (Opcional) oculta la parte final de las direcciones MAC.
Solo usa la biblioteca estándar de Python: no necesita instalar nada.

Uso:
    python limpiar_har.py captura.har
    python limpiar_har.py captura.har --ocultar-macs
Genera 'captura_limpio.json' y muestra qué peticiones conservó. Revísalo antes de enviarlo.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SECRETO = re.compile(r"pass|pwd|psw|psk|pin|secret|token|cookie|auth|session|sid|key|cred", re.I)
NOMBRES_SECRETOS = {"id", "pin", "sn", "uid"}      # nombres cortos que también son secretos
# Formato de paneles que envían "clave valor" por líneas (p. ej. "cPskSecret MiClave").
LINEA_SECRETA = re.compile(r"(?im)^([A-Za-z]*(?:pass|psk|pin|secret|authkey|token|cred)[A-Za-z]*)( \d+)? [^\r\n]+")
ESTATICOS = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".css", ".woff", ".woff2", ".ttf", ".map")
SENSIBLES = {"cookie", "set-cookie", "authorization", "proxy-authorization"}
UTILES = ("content-type", "referer", "origin", "x-requested-with", "location", "server")
JS_UTIL = re.compile(r"login|encr|md5|sha|rsa|aes|crypt|auth|common|lib", re.I)
MAC = re.compile(r"((?:[0-9A-Fa-f]{2}([:-])){3})(?:[0-9A-Fa-f]{2}\2){2}[0-9A-Fa-f]{2}")


def es_secreto(nombre):
    return bool(SECRETO.search(nombre)) or nombre.lower() in NOMBRES_SECRETOS


def redactar_json(valor):
    if isinstance(valor, dict):
        return {k: "XXXX" if es_secreto(k) and isinstance(v, (str, int)) else redactar_json(v)
                for k, v in valor.items()}
    if isinstance(valor, list):
        return [redactar_json(v) for v in valor]
    return valor


def redactar_texto(texto):
    """Oculta secretos en JSON, formularios (a=1&b=2) o texto libre."""
    if not texto or SIN_OCULTAR:
        return texto
    texto = LINEA_SECRETA.sub(lambda m: f"{m.group(1)}{m.group(2) or ''} XXXX", texto)
    try:
        return json.dumps(redactar_json(json.loads(texto)), ensure_ascii=False)
    except ValueError:
        pass
    if "=" in texto and "<" not in texto[:50]:
        pares = parse_qsl(texto, keep_blank_values=True)
        if pares:
            return urlencode([(k, "XXXX" if es_secreto(k) else v) for k, v in pares])
    # HTML: <input name="...pass..." value="..."> y similares
    texto = re.sub(r"""(name=["'][^"']*(?:pass|token|key|sid)[^"']*["'][^>]*?value=["'])[^"']*""",
                   r"\1XXXX", texto, flags=re.I)
    return re.sub(r"""((?:pass\w*|pwd|token)["']?\s*[:=]\s*["']?)[^"'&\s<,]+""", r"\1XXXX", texto, flags=re.I)


def redactar_url(url):
    if SIN_OCULTAR:
        return url
    partes = urlsplit(url)
    consulta = urlencode([(k, "XXXX" if es_secreto(k) else v)
                          for k, v in parse_qsl(partes.query, keep_blank_values=True)])
    return urlunsplit((partes.scheme, partes.netloc, partes.path, consulta, ""))


def ocultar_macs(texto):
    return MAC.sub(lambda m: f"{m.group(1)}XX{m.group(2)}XX{m.group(2)}XX", texto) if texto else texto


SIN_OCULTAR = False   # solo se activa con --sin-ocultar (captura de login con clave TEMPORAL)


def es_estatico(entrada):
    ruta = urlsplit(entrada["request"]["url"]).path.lower()
    tipo = (entrada["response"]["content"].get("mimeType") or "").lower()
    return ruta.endswith(ESTATICOS) or tipo.startswith(("image/", "font/", "text/css"))


def limpiar_entrada(e, max_cuerpo, macs):
    req, resp = e["request"], e["response"]
    url = req["url"]
    es_js = urlsplit(url).path.lower().endswith(".js")
    if es_js and not JS_UTIL.search(url):
        return None                                  # JS genérico: no aporta
    post = req.get("postData") or {}
    cuerpo_req = post.get("text") or urlencode([(p["name"], p.get("value", "")) for p in post.get("params", [])])
    contenido = resp["content"]
    cuerpo_resp = "" if contenido.get("encoding") == "base64" else (contenido.get("text") or "")
    limite = max_cuerpo * 2 if es_js else max_cuerpo
    cuerpo_resp = redactar_texto(cuerpo_resp)[:limite]
    salida = {
        "metodo": req["method"],
        "url": redactar_url(url),
        "estado": resp["status"],
        "tipo_respuesta": contenido.get("mimeType"),
        "cabeceras_peticion": {h["name"]: h["value"] for h in req["headers"] if h["name"].lower() in UTILES},
        "cabeceras_respuesta": {h["name"]: h["value"] for h in resp["headers"] if h["name"].lower() in UTILES},
        "cabeceras_sensibles_presentes": sorted({h["name"].lower() for h in req["headers"] + resp["headers"]
                                                 if h["name"].lower() in SENSIBLES}),
        "cuerpo_peticion": redactar_texto(cuerpo_req),
        "cuerpo_respuesta": cuerpo_resp,
    }
    if macs:
        for k in ("cuerpo_peticion", "cuerpo_respuesta"):
            salida[k] = ocultar_macs(salida[k])
    return salida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("har")
    ap.add_argument("--ocultar-macs", action="store_true", help="enmascara la mitad final de cada MAC")
    ap.add_argument("--max-cuerpo", type=int, default=4000, help="máx. de caracteres por respuesta")
    ap.add_argument("--max-entradas", type=int, default=60)
    ap.add_argument("--sin-ocultar", action="store_true",
                    help="NO borra secretos. Solo para capturar el login con una contraseña TEMPORAL")
    args = ap.parse_args()
    global SIN_OCULTAR
    SIN_OCULTAR = args.sin_ocultar
    if SIN_OCULTAR:
        print("AVISO: modo --sin-ocultar. Úsalo solo si la contraseña del router es temporal.\n")

    ruta = Path(args.har)
    try:
        har = json.loads(ruta.read_text(encoding="utf-8"))
        entradas = har["log"]["entries"]
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"No pude leer el archivo HAR: {error}")

    limpias = [c for e in entradas if not es_estatico(e)
               if (c := limpiar_entrada(e, args.max_cuerpo, args.ocultar_macs))]
    limpias = limpias[-args.max_entradas:]
    destino = ruta.with_name(ruta.stem + "_limpio.json")
    destino.write_text(json.dumps({"origen": ruta.name, "entradas": limpias}, indent=2, ensure_ascii=False),
                       encoding="utf-8")

    print(f"{len(entradas)} peticiones en la captura -> {len(limpias)} conservadas.\n")
    for i, c in enumerate(limpias, 1):
        print(f"{i:>3}. {c['metodo']:<5}{c['estado']}  {urlsplit(c['url']).path}")
    print(f"\nGuardado en: {destino}\nRevísalo con un editor de texto antes de enviarlo.")


if __name__ == "__main__":
    main()
