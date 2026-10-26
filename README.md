# Excavamos una casa griega

Diorama 3D interactivo de una excavación arqueológica para Educación Primaria. El alumnado explora un yacimiento **ficticio** con tres catas (A: casa griega; B: muro romano y zanja de expolio; C: sondeo profundo), selecciona hallazgos, separa **lo que vemos** de **lo que pensamos**, reproduce la formación y la excavación de las capas en una línea de tiempo y correlaciona los cortes de las tres zonas.

- **Usar en línea:** activar GitHub Pages (véase más abajo) y abrir `https://danielulpgc.github.io/DanielULPGC-Excavamos-casa-griega/`.
- **Usar sin conexión:** descargar [`descargas/excavacion-casa-griega.html`](descargas/excavacion-casa-griega.html) y abrirlo con doble clic. Es un único fichero con todo incrustado (Three.js y tipografías); no necesita internet ni instalación.
- **Guía docente e informe de auditoría didáctica:** [documento en línea](https://claude.ai/artifact/SH9r3jWFM8zz1gDLMDhDvn).

| Aspecto | Descripción |
| --- | --- |
| Destinatarios | Educación Primaria (2.º y 3.er ciclo). Hipótesis de uso **no validada con alumnado** |
| Idiomas | Español e inglés |
| Requisitos | Navegador actual con WebGL. Recomendable tableta o pantalla grande |
| Datos personales | No se recogen ni se envían. El cuaderno de campo se guarda solo en el navegador (`localStorage`) |
| Servicios externos en ejecución | Ninguno: Three.js y las fuentes se sirven desde el propio repositorio |

## Advertencias de contenido

El yacimiento es inventado y no reproduce ningún corte real. Las casas se inspiran en las de Olinto (Cahill, 2002; Nevett, 1999) y la secuencia griega y romana en la de Paestum, pero se mezclan rasgos de sitios distintos. Las escalas son didácticas (los objetos pequeños se agrandan; la altura de los muros de adobe es una suposición declarada). Las reconstrucciones se muestran siempre como **ideas** (volúmenes azules discontinuos), nunca como evidencia.

## Estructura del repositorio

```
index.html                         versión web (generada)
descargas/excavacion-casa-griega.html  fichero único sin conexión (generado)
fuente/plantilla.html              motor: HTML, CSS y JavaScript, sin contenido propio
datos/yacimiento.json              contenido: textos ES/EN, catas, capas, hallazgos, objetos, cronología, retos
vendor/three/                      Three.js r128 y OrbitControls (licencia MIT)
vendor/fuentes/                    Fredoka y Atkinson Hyperlegible en WOFF2 (licencia SIL OFL 1.1)
herramientas/construir.py          monta index.html y descargas/ a partir de fuente/ y datos/
herramientas/manifiesto.py         genera el manifiesto SHA-256
pruebas/pruebas_navegador.py       pruebas automáticas en Chromium (PASS/FAIL/BLOCKED/NOT_RUN)
.github/workflows/pruebas.yml      ejecuta las pruebas en cada cambio
MANIFIESTO-SHA256.txt              huellas de integridad de todos los ficheros
```

`index.html` y `descargas/` **no se editan a mano**: se generan. Para cambiar el yacimiento se edita `datos/yacimiento.json`; para cambiar el comportamiento, `fuente/plantilla.html`.

## Modificar el yacimiento

1. Edite `datos/yacimiento.json` (formato JSON: comillas dobles, sin coma tras el último elemento).
2. Para añadir un hallazgo hay que completar cuatro lugares: una entrada en `hallazgos`; su texto en `textos.es.finds` y `textos.en.finds`; su identificador en el `orden` de la cata; y un objeto en `objetos` con un `modelo` del catálogo y su posición `at` [x, z]. Escala: 1 unidad = 0,5 m; cada cata mide 10 × 10 unidades.
3. Reconstruya y compruebe:

```bash
python3 herramientas/construir.py
python3 herramientas/manifiesto.py
python3 pruebas/pruebas_navegador.py
```

El motor incluye un validador: si los datos citan capas, hallazgos o modelos inexistentes, o faltan textos en algún idioma, lo indica en la consola del navegador (tecla F12) y la prueba «validador interno» falla.

Catálogo de modelos 3D (24): `zocalo`, `muroMortero`, `muroAlineado`, `zanjaExpolio`, `sondeo`, `hoyoEnCorte`, `hogar`, `fragmentosAnfora`, `fragmentoCopa`, `fragmentosOlla`, `tejasCaidas`, `pesasTelar`, `restosComida`, `sigillata`, `tegulas`, `moneda`, `ceramicaMano`, `muestraCarbon`, `zonaPorExcavar`, `herramientas`, `marcaFin`, `reconstruccionesCasa`, `ideasCajas`, `ideaMuro`.

## Probar

Requisitos: Python 3.8+ y, para las pruebas, Playwright con Chromium y Pillow; Node.js solo para la prueba de accesibilidad.

```bash
pip install playwright pillow && python3 -m playwright install chromium
npm ci --ignore-scripts        # instala axe-core (opcional)
python3 pruebas/pruebas_navegador.py
```

Las pruebas comprueban: que no hay peticiones a servidores externos ni errores de JavaScript; que el validador de datos no detecta problemas y sí detecta errores sembrados a propósito; que la escena 3D se dibuja; las seis pestañas, las cuatro vistas de zona, las fichas de cada etiqueta, el cambio de idioma y la línea de tiempo; la accesibilidad automática (axe-core, WCAG 2.1 AA) en escritorio; la ausencia de desbordamiento horizontal a 390 px; y que el fichero sin conexión funciona con la red bloqueada.

Última ejecución local (26-10-2026, Chromium con renderizado por software): **15 PASS, 0 FAIL**. Estas pruebas son automáticas y no sustituyen la prueba con alumnado ni la evaluación con personas usuarias de lectores de pantalla.

## Publicar con GitHub Pages

*Settings → Pages → Build and deployment → Source: «Deploy from a branch» → Branch: `main`, carpeta `/ (root)` → Save.* El fichero `.nojekyll` evita el procesamiento con Jekyll. GitHub Pages en cuentas gratuitas requiere que el repositorio sea público.

**Privacidad.** El recurso no recoge datos, pero GitHub, como servidor, puede registrar la dirección IP de quien visita la página ([declaración de privacidad de GitHub](https://docs.github.com/es/site-policy/privacy-policies/github-general-privacy-statement)). Para uso con alumnado menor de edad conviene consultarlo con la persona delegada de protección de datos del centro o de la universidad; la alternativa sin terceros es el fichero sin conexión de `descargas/`, o alojarlo en un servidor institucional o en Moodle.

## Integridad

```bash
sha256sum -c MANIFIESTO-SHA256.txt
```

## Licencias

Véase [LICENCIA.md](LICENCIA.md). Componentes de terceros: Three.js r128 (MIT, © 2010-2021 three.js authors), Fredoka (SIL OFL 1.1, © The Fredoka Project Authors) y Atkinson Hyperlegible (SIL OFL 1.1, © Braille Institute of America). Sus textos de licencia acompañan a cada componente en `vendor/`.

## Referencias de la base arqueológica

- Cahill, N. (2002). *Household and City Organization at Olynthus*. Yale University Press.
- Nevett, L. C. (1999). *House and Society in the Ancient Greek World*. Cambridge University Press.
- Harris, E. C. (1989). *Principles of Archaeological Stratigraphy* (2.ª ed.). Academic Press.
- Zeder, M. A. y Lapham, H. A. (2010). Assessing the reliability of criteria used to identify postcranial bones in sheep, *Ovis*, and goats, *Capra*. *Journal of Archaeological Science, 37*, 2887-2905. https://doi.org/10.1016/j.jas.2010.06.032
- Evershed, R. P. (2008). Organic residue analysis in archaeology: the archaeological biomarker revolution. *Archaeometry, 50*(6), 895-924. https://doi.org/10.1111/j.1475-4754.2008.00446.x
- *The London Charter for the Computer-Based Visualisation of Cultural Heritage* (2009), versión 2.1.
