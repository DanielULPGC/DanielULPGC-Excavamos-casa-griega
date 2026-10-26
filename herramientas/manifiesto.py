#!/usr/bin/env python3
"""Genera MANIFIESTO-SHA256.txt (formato de «sha256sum») con todos los ficheros versionados.

Uso:   python3 herramientas/manifiesto.py
Comprobar una copia descargada:   sha256sum -c MANIFIESTO-SHA256.txt
(En Windows PowerShell: Get-FileHash -Algorithm SHA256 <fichero>)
"""
import hashlib, pathlib, subprocess

RAIZ = pathlib.Path(__file__).resolve().parent.parent
NOMBRE = "MANIFIESTO-SHA256.txt"
ficheros = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=RAIZ,
                          capture_output=True, text=True, check=True).stdout.split("\n")
ficheros = sorted({f for f in ficheros if f and f != NOMBRE})
lineas = ["%s  %s" % (hashlib.sha256((RAIZ / f).read_bytes()).hexdigest(), f) for f in ficheros]
(RAIZ / NOMBRE).write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("%d ficheros en %s" % (len(lineas), NOMBRE))
