"""Envía por email las licitaciones nuevas del día a cada suscriptor de pago, según sus filtros.

Los suscriptores se guardan en el secreto SUSCRIPTORES de GitHub (nunca en el repositorio), como JSON:
[
  {"email": "cliente@empresa.es", "nombre": "Instalaciones Pérez", "plan": "pro",
   "sectores": ["Fotovoltaica y autoconsumo"], "comunidades": ["Comunidad de Madrid"],
   "presupuestoMinimo": 20000, "palabras": ["colegio"]}
]
"plan" es "pro" o "empresa". "vertical" es la web a la que se suscribió ("energia", por defecto, o
"comunicacion"; ver web/verticales.py). Los suscriptores "empresa" reciben además, los lunes, el ranking completo
de empresas adjudicatarias en CSV. Una lista vacía o un filtro ausente significa "todo".

Variables: SMTP_HOST, SMTP_PORT (465), SMTP_USER, SMTP_PASS, REMITENTE.
Lee web/privado/<vertical>/nuevas_hoy.json y ranking_completo.json.
Con --prueba no envía nada: escribe los correos en web/privado/correos/.
"""
from __future__ import annotations

import argparse
import csv
import html
import io
import re
import sys
import json
import os
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage

from src.filtros import normalizar


def _euros(v) -> str:
    if v in (None, ""):
        return "sin importe publicado"
    return f"{v:,.0f} €".replace(",", ".")


def filtrar(licitaciones: list[dict], s: dict) -> list[dict]:
    sectores = set(s.get("sectores") or [])
    comunidades = set(s.get("comunidades") or [])
    minimo = s.get("presupuestoMinimo")
    palabras = [normalizar(p) for p in s.get("palabras") or [] if p.strip()]
    salida = []
    for r in licitaciones:
        if sectores and not sectores.intersection(r.get("sectores") or []):
            continue
        if comunidades and r.get("comunidadAutonoma") not in comunidades:
            continue
        importe = r.get("presupuestoSinIva") or r.get("valorEstimado")
        if minimo and (importe is None or importe < minimo):
            continue
        if palabras and not any(p in normalizar(r.get("titulo") or "") for p in palabras):
            continue
        salida.append(r)
    return salida


def cuerpo_html(nombre: str, lista: list[dict], url_web: str) -> str:
    filas = []
    for r in lista:
        plazo = r.get("fechaLimite") or "sin fecha"
        filas.append(
            f'<tr><td style="padding:10px 0;border-bottom:1px solid #d9dee5">'
            f'<a href="{html.escape(r.get("urlDetalle") or url_web)}" style="color:#2456a6;font-weight:600">'
            f'{html.escape(r.get("titulo") or "")}</a><br>'
            f'<span style="color:#4a5563">{html.escape(r.get("organoContratacion") or "")} · '
            f'{html.escape(r.get("comunidadAutonoma") or "")}</span><br>'
            f'<span>{_euros(r.get("presupuestoSinIva") or r.get("valorEstimado"))} · plazo hasta {plazo}</span>'
            f'</td></tr>'
        )
    return (
        f'<div style="font-family:Arial,sans-serif;color:#1b2430;max-width:640px">'
        f'<p>Hola {html.escape(nombre or "")}:</p>'
        f'<p>Hoy hay <b>{len(lista)}</b> {"licitación nueva que encaja" if len(lista) == 1 else "licitaciones nuevas que encajan"} con tu alerta.</p>'
        f'<table style="width:100%;border-collapse:collapse">{"".join(filas)}</table>'
        f'<p style="color:#4a5563;font-size:13px">Puedes ver todas las abiertas en <a href="{url_web}">{url_web}</a>. '
        f'Para cambiar tus filtros o darte de baja, responde a este correo.</p></div>'
    )


def ranking_csv(ranking: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Empresa", "NIF", "Contratos ganados", "Importe adjudicado (€)", "Comunidades", "Sectores"])
    for e in ranking:
        w.writerow([e["nombre"], e["nif"], e["contratos"], str(e["importe"]).replace(".", ","),
                    ", ".join(e["comunidades"]), ", ".join(e["sectores"])])
    return ("﻿" + buf.getvalue()).encode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--privado", default="web/privado")
    ap.add_argument("--prueba", action="store_true")
    args = ap.parse_args()

    suscriptores = json.loads(os.environ.get("SUSCRIPTORES") or "[]")
    if not suscriptores:
        print("Sin suscriptores: no se envía nada.")
        return
    from web.verticales import VERTICALES, url_vertical

    datos = {}
    for clave in VERTICALES:
        carpeta = os.path.join(args.privado, clave)
        if os.path.exists(os.path.join(carpeta, "nuevas_hoy.json")):
            with open(os.path.join(carpeta, "nuevas_hoy.json"), encoding="utf-8") as f:
                nuevas = json.load(f)
            with open(os.path.join(carpeta, "ranking_completo.json"), encoding="utf-8") as f:
                datos[clave] = (nuevas, json.load(f))
    remitente_base = os.environ.get("REMITENTE") or os.environ.get("SMTP_USER", "")
    es_lunes = date.today().weekday() == 0

    mensajes = []
    for s in suscriptores:
        clave = s.get("vertical") or "energia"
        if clave not in datos:
            print(f"Suscriptor con vertical desconocida o sin datos: {clave}", file=sys.stderr)
            continue
        nuevas, ranking = datos[clave]
        url_web = url_vertical(clave)
        tema = VERTICALES[clave]["config"]["tema"]
        # Mismo buzón, con el nombre de la web a la que está suscrito.
        remitente = re.sub(r"^[^<]*<", f'{VERTICALES[clave]["config"]["nombre"]} <', remitente_base) \
            if "<" in remitente_base else remitente_base
        lista = filtrar(nuevas, s)
        adjuntar = s.get("plan") == "empresa" and es_lunes
        if not lista and not adjuntar:
            continue
        m = EmailMessage()
        m["From"] = remitente
        m["To"] = s["email"]
        n = len(lista)
        m["Subject"] = ((f"{n} licitación {tema} nueva para ti" if n == 1 else
                         f"{n} licitaciones {tema} nuevas para ti") if lista
                        else "Ranking semanal de empresas adjudicatarias")
        m.set_content(m["Subject"] + ". Abre el correo en HTML para verlas.")
        m.add_alternative(cuerpo_html(s.get("nombre", ""), lista, url_web), subtype="html")
        if adjuntar:
            m.add_attachment(ranking_csv(ranking), maintype="text", subtype="csv",
                             filename=f"ranking-adjudicatarios-{date.today().isoformat()}.csv")
        mensajes.append(m)

    if args.prueba:
        carpeta = os.path.join(args.privado, "correos")
        os.makedirs(carpeta, exist_ok=True)
        for i, m in enumerate(mensajes):
            with open(os.path.join(carpeta, f"{i:03d}.eml"), "wb") as f:
                f.write(bytes(m))
        print(f"Modo prueba: {len(mensajes)} correos escritos en {carpeta}")
        return

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "465")), context=contexto) as srv:
        usuario, clave = os.environ["SMTP_USER"].strip(), os.environ["SMTP_PASS"].strip()
        if not (usuario.isascii() and clave.isascii()):
            raise SystemExit("SMTP_USER o SMTP_PASS tiene caracteres no válidos (tildes, ª, º...): "
                             "vuelve a pegarlos copiándolos del CSV de SES.")
        srv.login(usuario, clave)
        for m in mensajes:
            srv.send_message(m)
    print(f"Enviados {len(mensajes)} correos a {len(suscriptores)} suscriptores.")


if __name__ == "__main__":
    main()
