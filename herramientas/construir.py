#!/usr/bin/env python3
"""Construye el recurso a partir de la plantilla del motor y del archivo de datos.

Uso:
    python3 herramientas/construir.py            # genera index.html y descargas/
    python3 herramientas/construir.py --comprobar # falla si lo generado no coincide con lo guardado

Entradas:
    fuente/plantilla.html   motor (HTML, CSS y JavaScript) con tres marcadores
    datos/yacimiento.json   contenido del yacimiento (textos, catas, hallazgos...)
    vendor/                 Three.js r128 y fuentes tipográficas autoalojadas

Salidas:
    index.html                                   versión web (carga vendor/ por rutas relativas)
    descargas/excavacion-casa-griega.html        fichero único sin conexión (todo incrustado)

No usa dependencias externas: solo la biblioteca estándar de Python 3.8+.
"""
import base64, json, pathlib, sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FUENTES = [  # (familia, peso, estilo, fichero sin subconjunto)
    ("Fredoka", 500, "normal", "fredoka-{s}-500-normal.woff2"),
    ("Fredoka", 600, "normal", "fredoka-{s}-600-normal.woff2"),
    ("Atkinson Hyperlegible", 400, "normal", "atkinson-hyperlegible-{s}-400-normal.woff2"),
    ("Atkinson Hyperlegible", 700, "normal", "atkinson-hyperlegible-{s}-700-normal.woff2"),
    ("Atkinson Hyperlegible", 400, "italic", "atkinson-hyperlegible-{s}-400-italic.woff2"),
]
RANGOS = {
    "latin-ext": "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF",
    "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
}
CDN_FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
               '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
               '<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Fredoka:wght@500;600&display=swap" rel="stylesheet">')
CDN_THREE = ('<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>\n'
             '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>')


def leer(rel, binario=False):
    p = RAIZ / rel
    return p.read_bytes() if binario else p.read_text(encoding="utf-8")


def css_fuentes(incrustar):
    reglas = []
    for fam, peso, estilo, patron in FUENTES:
        for sub in ("latin-ext", "latin"):
            nombre = patron.format(s=sub)
            if incrustar:
                url = "data:font/woff2;base64," + base64.b64encode(leer("vendor/fuentes/" + nombre, True)).decode()
            else:
                url = nombre
            reglas.append(
                "@font-face{font-family:'%s';font-style:%s;font-display:swap;font-weight:%d;"
                "src:url(%s) format('woff2');unicode-range:%s;}" % (fam, estilo, peso, url, RANGOS[sub]))
    return "\n".join(reglas) + "\n"


def datos():
    texto = leer("datos/yacimiento.json")
    json.loads(texto)  # falla aquí si el JSON no es válido
    if "</" in texto:
        texto = texto.replace("</", "<\\/")  # impide cerrar el <script> desde los datos
    return texto


def montar(variante):
    h = leer("fuente/plantilla.html")
    for marca in ("{{YACIMIENTO}}", "{{FUENTES}}", "{{THREE}}"):
        if h.count(marca) != 1:
            sys.exit("plantilla: el marcador %s debe aparecer exactamente una vez" % marca)
    h = h.replace("{{YACIMIENTO}}", datos())
    if variante == "web":
        fu = '<link rel="stylesheet" href="vendor/fuentes/fuentes.css">'
        th = ('<script src="vendor/three/three.min.js"></script>\n'
              '<script src="vendor/three/OrbitControls.js"></script>')
    elif variante == "offline":
        fu = "<style>\n" + css_fuentes(True) + "</style>"
        th = ("<script>/* three.js r128 · MIT · (c) 2010-2021 three.js authors */\n" + leer("vendor/three/three.min.js") +
              "\n</script>\n<script>/* OrbitControls · three.js r128 · MIT */\n" + leer("vendor/three/OrbitControls.js") + "\n</script>")
    elif variante == "cdn":
        fu, th = CDN_FUENTES, CDN_THREE
    else:
        raise ValueError(variante)
    return h.replace("{{FUENTES}}", fu).replace("{{THREE}}", th)


SALIDAS = {
    "index.html": lambda: montar("web"),
    "descargas/excavacion-casa-griega.html": lambda: montar("offline"),
    "vendor/fuentes/fuentes.css": lambda: css_fuentes(False),
}


def main():
    comprobar = "--comprobar" in sys.argv
    malos = []
    for rel, f in SALIDAS.items():
        nuevo = f()
        p = RAIZ / rel
        if comprobar:
            if not p.exists() or p.read_text(encoding="utf-8") != nuevo:
                malos.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(nuevo, encoding="utf-8")
            print("escrito", rel, len(nuevo.encode()), "bytes")
    if comprobar:
        if malos:
            sys.exit("Desfasados respecto a fuente/ y datos/: " + ", ".join(malos) +
                     "\nEjecuta: python3 herramientas/construir.py")
        print("OK: index.html y descargas/ coinciden con fuente/ y datos/")


if __name__ == "__main__":
    main()
