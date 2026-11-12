"""Publica en el canal de Telegram las licitaciones nuevas del día de la web de energía.

Lee web/privado/energia/nuevas_hoy.json (lo genera web.generar_datos) y publica una por mensaje,
las de mayor importe primero, hasta MAXIMO al día; si hay más, un último mensaje remite a la web.

Variables (secretos de GitHub): TELEGRAM_TOKEN (token del bot) y TELEGRAM_CANAL (p. ej. @licitacionesenergia).
Con --prueba no publica nada: muestra los mensajes por pantalla.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request

MAXIMO = 10
URL_WEB = os.environ.get("URL_WEB", "https://ijfa1982.github.io/licitaciones-energia")


def _euros(v) -> str:
    if v in (None, ""):
        return "importe no publicado"
    return f"{v:,.0f} € sin IVA".replace(",", ".")


def _importe(r: dict) -> float:
    return r.get("presupuestoSinIva") or r.get("valorEstimado") or 0


def _fecha(v) -> str:
    v = str(v or "")
    return f"{v[8:10]}/{v[5:7]}/{v[0:4]}" if len(v) >= 10 and v[4] == "-" and v[7] == "-" else (v or "sin fecha publicada")


def mensaje(r: dict) -> str:
    e = html.escape
    lineas = [f"⚡ <b>{e(r.get('titulo') or 'Licitación')}</b>"]
    organo = " · ".join(x for x in (r.get("organoContratacion"), r.get("comunidadAutonoma")) if x)
    if organo:
        lineas.append(f"🏛 {e(organo)}")
    lineas.append(f"💶 {_euros(r.get('presupuestoSinIva') or r.get('valorEstimado'))}")
    lineas.append(f"⏳ Plazo hasta {e(_fecha(r.get('fechaLimite')))}")
    if r.get("urlDetalle"):
        lineas.append(f'🔗 <a href="{e(r["urlDetalle"])}">Ver la licitación</a>')
    return "\n".join(lineas)


def resumen(restantes: int) -> str:
    return (f"➕ Hoy hay {restantes} licitaciones nuevas más. Consúltalas y filtra por sector y comunidad en "
            f'<a href="{URL_WEB}">Licitaciones de Energía</a> · Arcas Lab')


def enviar(token: str, canal: str, texto: str) -> None:
    datos = urllib.parse.urlencode({"chat_id": canal, "text": texto, "parse_mode": "HTML",
                                    "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=datos)
    with urllib.request.urlopen(req, timeout=30) as r:
        if not json.load(r).get("ok"):
            raise RuntimeError("Telegram rechazó el mensaje")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--privado", default="web/privado")
    ap.add_argument("--vertical", default="energia")
    ap.add_argument("--prueba", action="store_true")
    args = ap.parse_args()

    ruta = os.path.join(args.privado, args.vertical, "nuevas_hoy.json")
    if not os.path.exists(ruta):
        print(f"No existe {ruta}: nada que publicar")
        return
    with open(ruta, encoding="utf-8") as f:
        nuevas = sorted(json.load(f), key=_importe, reverse=True)
    if not nuevas:
        print("Hoy no hay licitaciones nuevas")
        return

    textos = [mensaje(r) for r in nuevas[:MAXIMO]]
    if len(nuevas) > MAXIMO:
        textos.append(resumen(len(nuevas) - MAXIMO))

    if args.prueba:
        print("\n\n".join(textos))
        return
    token, canal = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CANAL")
    if not token or not canal:
        sys.exit("Faltan TELEGRAM_TOKEN o TELEGRAM_CANAL")
    errores = 0
    for t in textos:
        try:
            enviar(token, canal, t)
        except Exception as ex:  # un mensaje fallido no debe parar el resto
            errores += 1
            print(f"Error al publicar: {ex}")
        time.sleep(3)  # margen frente al límite de mensajes por minuto de Telegram
    print(f"Publicados {len(textos) - errores} de {len(textos)} mensajes en {canal}")


if __name__ == "__main__":
    main()
