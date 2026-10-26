#!/usr/bin/env python3
"""Pruebas automáticas en navegador real (Chromium, mediante Playwright).

Uso:
    pip install playwright && python3 -m playwright install chromium   (una vez)
    npm install                                                        (opcional: activa la prueba de accesibilidad)
    python3 pruebas/pruebas_navegador.py

Cada prueba informa PASS, FAIL, BLOCKED o NOT_RUN con su evidencia.
El programa termina con código 1 si alguna prueba da FAIL.
"""
import functools, http.server, json, pathlib, re, sys, threading

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RES = []


def informar(nombre, estado, evidencia=""):
    RES.append((nombre, estado, evidencia))
    print("%-8s %s%s" % (estado, nombre, (" · " + evidencia) if evidencia else ""), flush=True)


def servidor():
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Silencioso, directory=str(RAIZ))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d/" % s.server_address[1]


def abrir(br, url, ancho=1366, alto=860, bloquear_externo=True):
    ctx = br.new_context(viewport={"width": ancho, "height": alto})
    pg = ctx.new_page()
    reg = {"externas": [], "errores": [], "avisos": []}

    def ruta(route):
        u = route.request.url
        if u.startswith(("http://127.0.0.1", "file:", "data:", "blob:")):
            route.continue_()
        else:
            reg["externas"].append(u)
            route.abort() if bloquear_externo else route.continue_()
    pg.route("**/*", ruta)
    pg.on("pageerror", lambda e: reg["errores"].append(str(e)))
    pg.on("console", lambda m: (reg["errores"] if m.type == "error" else reg["avisos"]).append(m.text)
          if m.type in ("error", "warning") else None)
    pg.goto(url)
    pg.wait_for_timeout(2500)
    return ctx, pg, reg


def pixeles_pintados(pg):
    """Cuenta tonos distintos en una captura del lienzo (WebGL no conserva el búfer para leerlo)."""
    import io
    try:
        from PIL import Image
    except ImportError:
        return -1
    im = Image.open(io.BytesIO(pg.locator("#c").screenshot())).convert("RGB").resize((96, 60))
    d = im.tobytes()
    return len({(d[i] >> 4, d[i + 1] >> 4, d[i + 2] >> 4) for i in range(0, len(d), 3)})


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        informar("todas", "BLOCKED", "Playwright no está instalado")
        return 1
    srv, base = servidor()
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])

        # 1. Versión web: arranque limpio y sin servicios externos
        ctx, pg, reg = abrir(br, base + "index.html")
        informar("web · sin peticiones externas", "PASS" if not reg["externas"] else "FAIL",
                 "; ".join(reg["externas"][:3]) or "0 peticiones fuera del servidor")
        informar("web · sin errores de JavaScript", "PASS" if not reg["errores"] else "FAIL",
                 "; ".join(reg["errores"][:3]) or "0 errores")
        val = [a for a in reg["avisos"] if a.startswith("[yacimiento]")]
        informar("datos · validador interno sin problemas", "PASS" if not val else "FAIL", val[0][:200] if val else "0 problemas")
        n = pixeles_pintados(pg)
        if n < 0:
            informar("web · escena 3D dibujada", "NOT_RUN", "falta Pillow (pip install pillow)")
        elif pg.is_visible("#nogl"):
            informar("web · escena 3D dibujada", "BLOCKED", "el navegador de prueba no ofrece WebGL")
        else:
            informar("web · escena 3D dibujada", "PASS" if n > 20 else "FAIL", "%d tonos distintos en el lienzo" % n)

        # 2. Pestañas
        malas = []
        for t in ["tiempo", "cuaderno", "epocas", "conjunto", "retos", "explorar"]:
            pg.click("#tab-" + t); pg.wait_for_timeout(250)
            if pg.get_attribute("#tab-" + t, "aria-selected") != "true" or not pg.inner_text("#panelInner").strip():
                malas.append(t)
        informar("interfaz · seis pestañas", "PASS" if not malas else "FAIL", "fallan: " + ", ".join(malas) if malas else "6/6 responden")

        # 3. Zonas A, B, C y Plano
        malas = []
        for s in ["B", "C", "ALL", "A"]:
            pg.click('#secbar button[data-sec="%s"]' % s); pg.wait_for_timeout(500)
            if pg.get_attribute('#secbar button[data-sec="%s"]' % s, "aria-pressed") != "true":
                malas.append(s)
        informar("interfaz · cambio de zona", "PASS" if not malas else "FAIL", "fallan: " + ", ".join(malas) if malas else "A, B, C y Plano")

        # 4. Seleccionar hallazgos desde las etiquetas (y que no salte de zona)
        pg.click('#dock button[data-act="home"]'); pg.wait_for_timeout(1500)
        ids = pg.evaluate("[...document.querySelectorAll('#labels button.tag')].filter(b=>b.offsetParent&&b.dataset.id&&getComputedStyle(b).visibility==='visible').map(b=>b.dataset.id)")
        if not ids:
            informar("interfaz · fichas de hallazgos", "BLOCKED", "no hay etiquetas visibles (¿sin WebGL?)")
        else:
            malos = []
            for fid in ids:
                pg.click('#dock button[data-act="home"]'); pg.wait_for_timeout(1500)  # vista inicial: las etiquetas fuera de encuadre se ocultan a propósito
                try:
                    pg.click('#labels button[data-id="%s"]' % fid, timeout=4000)
                except Exception as e:
                    malos.append("%s: no se puede pulsar (%s)" % (fid, str(e).splitlines()[0][:60])); continue
                pg.wait_for_timeout(250)
                nombre = (pg.get_attribute('#labels button[data-id="%s"]' % fid, "aria-label") or "").split(": ", 1)[-1]
                titulo = pg.inner_text("#panelTitle") if pg.locator("#panelTitle").count() else ""
                if titulo.strip() != nombre.strip():
                    malos.append("%s→«%s»" % (fid, titulo))
            informar("interfaz · fichas de hallazgos", "PASS" if not malos else "FAIL",
                     "; ".join(malos[:3]) if malos else "%d/%d etiquetas abren su propia ficha" % (len(ids), len(ids)))
        pg.click('#secbar button[data-sec="C"]'); pg.wait_for_timeout(500)
        informar("interfaz · la zona C se mantiene al pulsar", "PASS" if pg.get_attribute('#secbar button[data-sec="C"]', "aria-pressed") == "true" else "FAIL")

        # 5. Idioma
        pg.click('button[data-lang="en"]'); pg.wait_for_timeout(300)
        en = pg.get_attribute("html", "lang")
        pg.click('button[data-lang="es"]'); pg.wait_for_timeout(300)
        informar("interfaz · cambio de idioma ES/EN", "PASS" if en == "en" and pg.get_attribute("html", "lang") == "es" else "FAIL", "lang=" + str(en))

        # 6. Línea de tiempo: reproduce y se detiene
        pg.click("#tab-tiempo"); pg.wait_for_timeout(300)
        if pg.is_visible("#tlRange"):
            pg.fill("#tlRange", "0"); pg.dispatch_event("#tlRange", "input"); pg.wait_for_timeout(200)
            v0 = float(pg.input_value("#tlRange"))
            pg.click("#tlPlay"); pg.wait_for_timeout(2500)
            v1 = float(pg.input_value("#tlRange"))
            informar("tiempo · la línea de tiempo avanza", "PASS" if v1 > v0 else "FAIL", "%.2f → %.2f" % (v0, v1))
        else:
            informar("tiempo · la línea de tiempo avanza", "FAIL", "#tlRange no visible en la pestaña Tiempo")
        nuevos = [e for e in reg["errores"]]
        informar("interfaz · sin errores tras el recorrido", "PASS" if not nuevos else "FAIL", "; ".join(nuevos[:3]) or "0 errores")

        # 7. Accesibilidad (axe-core), si está instalado
        axe = RAIZ / "node_modules/axe-core/axe.min.js"
        if axe.exists():
            pg.click("#tab-explorar"); pg.add_script_tag(path=str(axe))
            r = pg.evaluate("async () => (await axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa']})).violations.map(v=>v.id+':'+v.nodes.length)")
            informar("accesibilidad · axe WCAG 2.1 AA (escritorio)", "PASS" if not r else "FAIL", ", ".join(r) or "0 infracciones")
        else:
            informar("accesibilidad · axe WCAG 2.1 AA (escritorio)", "NOT_RUN", "ejecuta «npm install» para activarla")
        ctx.close()

        # 8. Móvil
        ctx, pg, reg = abrir(br, base + "index.html", 390, 844)
        ancho = pg.evaluate("document.documentElement.scrollWidth")
        informar("móvil · sin desbordamiento horizontal (390 px)", "PASS" if ancho <= 390 and not reg["errores"] else "FAIL", "scrollWidth=%s" % ancho)
        ctx.close()

        # 9. Fichero único sin conexión (file://, red bloqueada)
        ctx, pg, reg = abrir(br, (RAIZ / "descargas/excavacion-casa-griega.html").as_uri())
        ok = not reg["externas"] and not reg["errores"] and not pg.is_visible("#nogl") and pixeles_pintados(pg) > 20
        informar("sin conexión · fichero único funciona", "PASS" if ok else "FAIL",
                 "externas=%d errores=%d" % (len(reg["externas"]), len(reg["errores"])))
        ctx.close()

        # 10. El validador detecta datos erróneos (prueba de mutación)
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        mal = html.replace('"modelo": "zocalo"', '"modelo": "noExiste"', 1).replace('"cata": "B"', '"cata": "Z"', 1)
        ctx = br.new_context(); pg = ctx.new_page(); av = []
        pg.on("console", lambda m: av.append(m.text) if m.type == "warning" else None)
        pg.route("**/mutado.html", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=mal))
        pg.goto(base + "mutado.html"); pg.wait_for_timeout(2000)
        txt = " ".join(a for a in av if a.startswith("[yacimiento]"))
        det = ("noExiste" in txt) + ("«Z»" in txt)
        informar("datos · el validador detecta errores sembrados", "PASS" if det == 2 else "FAIL", "%d/2 errores detectados" % det)
        ctx.close()
        br.close()
    srv.shutdown()

    falla = any(e == "FAIL" for _, e, _ in RES)
    resumen = {e: sum(1 for _, x, _ in RES if x == e) for e in ("PASS", "FAIL", "BLOCKED", "NOT_RUN")}
    print("\nResumen:", json.dumps(resumen, ensure_ascii=False))
    (RAIZ / "pruebas/ultimo-resultado.json").write_text(
        json.dumps([{"prueba": n, "estado": e, "evidencia": v} for n, e, v in RES], ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if falla else 0


if __name__ == "__main__":
    sys.exit(main())
