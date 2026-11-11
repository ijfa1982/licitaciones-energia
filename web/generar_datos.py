"""Genera los datos de la web (licitaciones abiertas y adjudicaciones) a partir del feed oficial.

Se ejecuta a diario en GitHub Actions. Reutiliza el lector y los filtros del Actor de Apify, así que
la web y el Actor clasifican igual. Los datos del día anterior se descargan de la propia web publicada
para ir acumulando un histórico sin necesidad de base de datos.

Lee el feed una sola vez y reparte lo leído entre las webs de cada sector (web/verticales.py).

Uso:
    python -m web.generar_datos --salida web/build --privado web/privado
    (deja web/build/<vertical>/data/*.json y web/privado/<vertical>/*.json)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.catalogo import FEED_LICITACIONES
from src.catalogo import SECTORES
from src.filtros import Config, clasificar, dias_restantes
from src.main import MADRID, descargar, recorrer
from src.parser import parse_iso

DIAS_ADJUDICACIONES = 120   # histórico para el ranking de empresas
DIAS_PRIMERA_VEZ = 10       # cuánto se lee la primera vez, sin datos previos
TIEMPO_MAXIMO_LECTURA = 45 * 60  # segundos; si la Plataforma va lenta se para y publica lo leído
CAMPOS_LICITACION = [
    "id", "expediente", "titulo", "estado", "organoContratacion", "comunidadAutonoma", "codigoNuts",
    "municipio", "tipoContrato", "procedimiento", "presupuestoSinIva", "valorEstimado", "fechaLimite",
    "horaLimite", "sectores", "relevancia", "urlDetalle", "actualizado", "cpv",
]


def _leer_json(url: str) -> Optional[dict]:
    try:
        if url.startswith("http"):
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        with open(url, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 - la primera ejecución no tiene datos previos
        return None


def _recortar(rec: dict) -> dict:
    return {k: rec.get(k) for k in CAMPOS_LICITACION}


def reclasificar(lista: list[dict], cfg: Optional[Config] = None) -> list[dict]:
    """Vuelve a clasificar con el filtro actual (y los sectores de la vertical), descartando lo que no encaja."""
    cfg = cfg or Config()
    salida = []
    for r in lista:
        sectores, _, relevancia = clasificar(r, cfg)
        if sectores:
            salida.append({**r, "sectores": [SECTORES[s]["nombre"] if s in SECTORES else s for s in sectores],
                           "relevancia": relevancia})
    return salida


def combinar(previos: dict, nuevos: list[dict], hoy, cfg: Optional[Config] = None) -> tuple[list[dict], list[dict], list[dict]]:
    """Mezcla los datos previos con lo leído hoy. Devuelve (abiertas, adjudicaciones, nuevas_hoy)."""
    abiertas = {r["id"]: r for r in reclasificar(previos.get("abiertas", []), cfg)}
    adjudicaciones = {r["id"]: r for r in reclasificar(previos.get("adjudicaciones", []), cfg)}
    nuevos = reclasificar(nuevos, cfg)
    conocidas = set(abiertas) | set(adjudicaciones)
    nuevas_hoy = []

    for rec in nuevos:
        clave = rec.get("id") or rec.get("expediente")
        if not clave:
            continue
        estado = rec.get("estado")
        if estado in ("ADJ", "RES"):
            abiertas.pop(clave, None)
            ganadores = rec.get("adjudicatarios") or []
            if not ganadores and rec.get("adjudicatario"):
                ganadores = [{"nombre": rec["adjudicatario"], "nif": rec.get("adjudicatarioNif"),
                              "importeSinIva": rec.get("importeAdjudicacion")}]
            d = _recortar(rec)
            d["adjudicatarios"] = [
                {"nombre": g.get("nombre"), "nif": g.get("nif"), "importe": g.get("importeSinIva"),
                 "lote": g.get("lote")} for g in ganadores if g.get("nombre")
            ]
            if d["adjudicatarios"]:
                adjudicaciones[clave] = d
        elif estado in ("PUB", "PRE"):
            d = _recortar(rec)
            if clave not in conocidas:
                nuevas_hoy.append(d)
            abiertas[clave] = d
        else:  # EV (en evaluación), ANUL...: deja de estar abierta
            abiertas.pop(clave, None)

    def vigente(r):
        dias = dias_restantes(r.get("fechaLimite"), hoy)
        return dias is None or dias >= 0

    nuevas_hoy = [r for r in nuevas_hoy if vigente(r)]
    corte = (hoy - timedelta(days=DIAS_ADJUDICACIONES)).isoformat()
    abiertas_l = sorted((r for r in abiertas.values() if vigente(r)),
                        key=lambda r: (r.get("fechaLimite") or "9999", r.get("titulo") or ""))
    adj_l = sorted((r for r in adjudicaciones.values() if (r.get("actualizado") or "") >= corte),
                   key=lambda r: r.get("actualizado") or "", reverse=True)
    return abiertas_l, adj_l, nuevas_hoy


def ranking(adjudicaciones: list[dict]) -> list[dict]:
    """Empresas que más contratos de energía ganan (agrupadas por NIF o, si falta, por nombre)."""
    grupos: dict[str, dict] = {}
    for a in adjudicaciones:
        for g in a.get("adjudicatarios") or []:
            nif = (g.get("nif") or "").upper()
            clave = nif if len(nif) == 9 and "*" not in nif else (g.get("nombre") or "").upper()
            e = grupos.setdefault(clave, {"nombre": g.get("nombre"), "nif": nif if clave == nif else "",
                                          "contratos": 0, "importe": 0.0, "comunidades": {}, "sectores": {}})
            e["contratos"] += 1
            e["importe"] += g.get("importe") or 0
            ca = a.get("comunidadAutonoma") or "Sin comunidad"
            e["comunidades"][ca] = e["comunidades"].get(ca, 0) + 1
            for s in a.get("sectores") or []:
                e["sectores"][s] = e["sectores"].get(s, 0) + 1
    salida = []
    for e in grupos.values():
        e["comunidades"] = sorted(e["comunidades"], key=e["comunidades"].get, reverse=True)[:3]
        e["sectores"] = sorted(e["sectores"], key=e["sectores"].get, reverse=True)[:2]
        e["importe"] = round(e["importe"], 2)
        salida.append(e)
    salida.sort(key=lambda e: (-e["contratos"], -e["importe"]))
    return salida


async def leer_feed(desde_dias: int, ahora: datetime, log=print, sectores: Optional[list[str]] = None) -> list[dict]:
    cfg = Config(estados=["PUB", "PRE", "EV", "ADJ", "RES", "ANUL"], excluir_vencidas=False)
    if sectores:
        cfg.sectores = list(sectores)
    leidos: list[dict] = []

    async def guardar(lote):
        leidos.extend(lote)

    import time
    fin = time.monotonic() + TIEMPO_MAXIMO_LECTURA
    await recorrer([FEED_LICITACIONES], cfg, fetch=descargar, guardar=guardar, log=log,
                   max_paginas=150, dias_atras=desde_dias, max_resultados=100000, ahora=ahora,
                   segundos_restantes=lambda: fin - time.monotonic())
    return leidos


def guardar_vertical(salida: str, privado: str, ahora: datetime, previos: dict, nuevos: list[dict], hoy,
                     cfg: Config) -> dict:
    abiertas, adjudicaciones, nuevas_hoy = combinar(previos, nuevos, hoy, cfg)
    rank = ranking(adjudicaciones)
    os.makedirs(salida, exist_ok=True)
    os.makedirs(privado, exist_ok=True)
    datos = {"actualizado": ahora.isoformat(timespec="seconds"), "abiertas": abiertas,
             "adjudicaciones": adjudicaciones}
    # Lo que carga la web: abiertas completas y solo el top 10 del ranking (el ranking completo es de pago).
    publico = {"actualizado": datos["actualizado"], "abiertas": abiertas,
               "ranking": rank[:10], "empresasRanking": len(rank), "adjudicacionesAnalizadas": len(adjudicaciones),
               "nuevasHoy": len(nuevas_hoy)}
    for carpeta, nombre, contenido in ((salida, "datos.json", datos), (salida, "web.json", publico),
                                       (privado, "nuevas_hoy.json", nuevas_hoy),
                                       (privado, "ranking_completo.json", rank)):
        with open(os.path.join(carpeta, nombre), "w", encoding="utf-8") as f:
            json.dump(contenido, f, ensure_ascii=False, separators=(",", ":"))
    return {"abiertas": len(abiertas), "nuevas": len(nuevas_hoy), "adjudicaciones": len(adjudicaciones),
            "empresas": len(rank)}


def main() -> None:
    from web.verticales import VERTICALES, url_vertical

    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="web/build", help="carpeta con una subcarpeta por vertical")
    ap.add_argument("--privado", default="web/privado", help="carpeta que no se publica (alertas, CSV)")
    ap.add_argument("--sin-previos", action="store_true", help="no descargar los datos publicados ayer")
    args = ap.parse_args()

    ahora = datetime.now(timezone.utc)
    hoy = ahora.astimezone(MADRID).date()
    previos = {}
    dias = 2
    for clave in VERTICALES:
        p = None if args.sin_previos else _leer_json(f"{url_vertical(clave)}/data/datos.json")
        previos[clave] = p or {}
        ultima = parse_iso(p.get("actualizado")) if p else None
        # Un día de solape por el retraso con el que la Plataforma publica el feed.
        dias = max(dias, min(DIAS_PRIMERA_VEZ, (ahora - ultima).days + 2) if ultima else DIAS_PRIMERA_VEZ)
    todos = list(dict.fromkeys(s for v in VERTICALES.values() for s in v["sectores"]))
    print(f"Leyendo el feed: {dias} días hacia atrás para {len(VERTICALES)} webs")
    nuevos = asyncio.run(leer_feed(dias, ahora, sectores=todos))

    for clave, v in VERTICALES.items():
        cfg = Config(sectores=list(v["sectores"]))
        r = guardar_vertical(os.path.join(args.salida, clave, "data"), os.path.join(args.privado, clave),
                             ahora, previos[clave], nuevos, hoy, cfg)
        print(f"{clave}: abiertas {r['abiertas']} · nuevas hoy {r['nuevas']} · adjudicaciones "
              f"{r['adjudicaciones']} · empresas en ranking {r['empresas']}")


if __name__ == "__main__":
    main()
