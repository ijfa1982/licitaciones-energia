"""Descarga las fotos de la web desde Wikimedia Commons y genera los créditos.

Todas las fotos de Commons tienen licencia libre, pero casi todas exigen citar autor y licencia.
Este script lee esos datos de la API de Commons y los guarda en img/fotos/creditos.json, que la web
muestra en el pie. Se ejecuta en GitHub Actions antes de publicar. Para cambiar una foto, cambia el
nombre del archivo de Commons en FOTOS (lo que va detrás de "File:" en la página de la foto).
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "LicitacionesEnergia/1.0 (https://github.com/ijfa1982/licitaciones-energia)"

# Las fotos de cada web están en web/verticales.py (clave "fotos").


def _texto(valor: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", valor or "")).strip()


def metadatos(archivo: str, ancho: int = 1600) -> dict | None:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo", "titles": f"File:{archivo}",
        "iiprop": "url|extmetadata", "iiurlwidth": ancho,
    })
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = json.loads(r.read().decode("utf-8"))
    return extraer(datos)


def extraer(datos: dict) -> dict | None:
    for pagina in (datos.get("query", {}).get("pages") or {}).values():
        info = (pagina.get("imageinfo") or [None])[0]
        if not info:
            return None
        meta = info.get("extmetadata") or {}
        return {
            "url": info.get("thumburl") or info.get("url"),
            "pagina": info.get("descriptionurl"),
            "autor": _texto(meta.get("Artist", {}).get("value")) or "Autor desconocido",
            "licencia": _texto(meta.get("LicenseShortName", {}).get("value")),
            "urlLicencia": meta.get("LicenseUrl", {}).get("value", ""),
        }
    return None


def descargar_set(fotos: dict, carpeta: str) -> None:
    os.makedirs(carpeta, exist_ok=True)
    creditos = []
    for hueco, (archivo, alt) in fotos.items():
        try:
            m = metadatos(archivo)
            if not m or not m["url"]:
                raise ValueError("no encontrada")
            req = urllib.request.Request(m["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(os.path.join(carpeta, f"{hueco}.jpg"), "wb") as f:
                f.write(r.read())
            creditos.append({"hueco": hueco, "alt": alt, **m})
            print(f"{hueco}: {archivo} · {m['autor']} · {m['licencia']}")
        except Exception as e:  # noqa: BLE001 - una foto que falla no debe tumbar la publicación
            print(f"{hueco}: no se pudo descargar {archivo} ({e})", file=sys.stderr)
    with open(os.path.join(carpeta, "creditos.json"), "w", encoding="utf-8") as f:
        json.dump(creditos, f, ensure_ascii=False, indent=1)


def main(base: str = "web/build") -> None:
    from web.verticales import VERTICALES
    for clave, v in VERTICALES.items():
        print(f"Fotos de {clave}:")
        descargar_set(v["fotos"], os.path.join(base, clave, "fotos"))


if __name__ == "__main__":
    main(*sys.argv[1:])
