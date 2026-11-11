"""Monta la web publicable (web/dist) con una copia de web/site por cada vertical.

Para cada vertical: copia la plantilla, aplica sus textos, sus tarjetas de sector y su config.js, y añade
sus datos (web/build/<vertical>/data), sus fotos (web/build/<vertical>/fotos) y el mapa común.
Falla si un texto a sustituir ya no existe en la plantilla, para que un cambio en index.html no deje
una web a medio traducir sin que nadie se entere.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys

from web.verticales import VERTICALES

PLANTILLA = "web/site"
IGNORAR = shutil.ignore_patterns("data", "fotos")


def tarjetas(sectores_html: list[tuple[str, str, str]]) -> str:
    from src.catalogo import SECTORES
    filas = []
    for clave, foto, corto in sectores_html:
        nombre = html.escape(SECTORES[clave]["nombre"])
        filas.append(
            f'    <button class="sector" data-sector="{nombre}"><img src="img/fotos/{foto}.jpg" alt="" '
            f'onerror="this.remove()"><span class="sector-nombre">{html.escape(corto)}</span>'
            f'<span class="sector-n"></span></button>'
        )
    return '<section class="sectores" aria-label="Buscar por sector">\n' + "\n".join(filas) + "\n  </section>"


def aplicar(texto: str, cambios: dict, archivo: str) -> str:
    for viejo, nuevo in cambios.items():
        if viejo in texto:
            texto = texto.replace(viejo, nuevo)
        elif archivo == "index.html" and not viejo.startswith("Sectores ("):
            raise SystemExit(f"{archivo}: no encuentro el texto a sustituir: {viejo[:70]!r}")
    return texto


def config_js(base: str, valores: dict) -> str:
    for clave, valor in valores.items():
        patron = re.compile(rf'^(\s*{clave}:\s*)"[^"]*"', re.M)
        if patron.search(base):
            base = patron.sub(lambda m: m.group(1) + json.dumps(valor, ensure_ascii=False), base)
        else:
            base = base.replace("window.CONFIG = {", f"window.CONFIG = {{\n  {clave}: {json.dumps(valor, ensure_ascii=False)},", 1)
    return base


def construir(build: str = "web/build", dist: str = "web/dist") -> None:
    if os.path.exists(dist):
        shutil.rmtree(dist)
    for clave, v in VERTICALES.items():
        destino = os.path.join(dist, v["ruta"]) if v["ruta"] else dist
        shutil.copytree(PLANTILLA, destino, ignore=IGNORAR, dirs_exist_ok=True)
        for archivo in ("index.html", "gracias.html", "legal.html", "manifest.webmanifest"):
            ruta = os.path.join(destino, archivo)
            texto = open(ruta, encoding="utf-8").read()
            texto = aplicar(texto, v.get("textos", {}), archivo)
            if archivo == "index.html" and v.get("sectores_html"):
                texto, n = re.subn(r'<section class="sectores".*?</section>', tarjetas(v["sectores_html"]),
                                   texto, count=1, flags=re.S)
                if not n:
                    raise SystemExit("index.html: no encuentro la sección de sectores")
            if archivo == "manifest.webmanifest":
                texto = texto.replace('"Licitaciones Energía"', json.dumps(v["config"]["nombre"], ensure_ascii=False))
            open(ruta, "w", encoding="utf-8").write(texto)
        ruta = os.path.join(destino, "config.js")
        contenido = config_js(open(ruta, encoding="utf-8").read(), v["config"])
        open(ruta, "w", encoding="utf-8").write(contenido)
        # Datos, fotos y mapa
        for origen, sub in ((os.path.join(build, clave, "data"), "data"),
                            (os.path.join(build, clave, "fotos"), os.path.join("img", "fotos"))):
            if os.path.isdir(origen):
                shutil.copytree(origen, os.path.join(destino, sub), dirs_exist_ok=True)
        if os.path.exists(os.path.join(build, "mapa.json")):
            os.makedirs(os.path.join(destino, "data"), exist_ok=True)
            shutil.copy(os.path.join(build, "mapa.json"), os.path.join(destino, "data", "mapa.json"))
        print(f"{clave}: {destino}")


if __name__ == "__main__":
    construir(*sys.argv[1:])
