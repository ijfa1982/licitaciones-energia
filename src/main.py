"""Actor de Apify: licitaciones públicas del sector energético en España (PLACSP)."""
from __future__ import annotations

import asyncio
import gzip
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from apify import Actor

from .catalogo import FEED_CONTRATOS_MENORES, FEED_LICITACIONES, HOSTS_OFICIALES
from .filtros import Config, evaluar
from .parser import parse_feed, parse_iso

USER_AGENT = "licitaciones-energia-espana/0.1 (Apify Actor; datos abiertos PLACSP)"
ESPERA_ENTRE_PAGINAS = 1.0  # segundos, para no cargar el servidor público
CLAVE_ESTADO = "VISTOS"
MADRID = ZoneInfo("Europe/Madrid")


def url_oficial(url: str) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and (p.hostname or "") in HOSTS_OFICIALES


def _descargar_sync(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data


async def descargar(url: str, intentos: int = 3) -> bytes:
    for i in range(intentos):
        try:
            return await asyncio.to_thread(_descargar_sync, url)
        except Exception:  # noqa: BLE001
            if i == intentos - 1:
                raise
            await asyncio.sleep(5 * (i + 1))
    raise RuntimeError("inalcanzable")


async def recorrer(
    feeds: list[str],
    cfg: Config,
    *,
    fetch: Callable[[str], Awaitable[bytes]],
    guardar: Callable[[list[dict]], Awaitable[None]],
    log: Callable[[str], None],
    max_paginas: int,
    dias_atras: int,
    max_resultados: int,
    ahora: datetime,
    vistos_previos: Optional[dict] = None,
) -> tuple[int, dict]:
    """Recorre las páginas de cada feed (de más reciente a más antigua) y guarda las coincidencias.

    Devuelve (número de resultados guardados, mapa expediente -> fecha de actualización vista).
    """
    hoy = ahora.astimezone(MADRID).date()
    limite = ahora - timedelta(days=dias_atras)
    entradas_vistas: set[str] = set()
    vistos: dict = dict(vistos_previos or {})
    total = 0

    for feed in feeds:
        url: Optional[str] = feed
        paginas = 0
        nombre_feed = feed.rsplit("/", 1)[-1]
        while url and paginas < max_paginas and total < max_resultados:
            if not url_oficial(url):
                log(f"URL descartada por no ser de la Plataforma oficial: {url}")
                break
            datos = await fetch(url)
            registros, siguiente, _ = parse_feed(datos)
            paginas += 1

            if paginas == 1 and registros:
                for r in registros[:3]:
                    log(
                        "Muestra: "
                        f"estado={r.get('estado')} actualizado={r.get('actualizado')} "
                        f"fechaLimite={r.get('fechaLimite')} cpv={r.get('cpv')} "
                        f"titulo={(r.get('titulo') or '')[:80]!r}"
                    )

            fechas = [d for d in (parse_iso(r.get("actualizado")) for r in registros) if d]
            descartes: Counter = Counter()
            lote: list[dict] = []
            for rec in registros:
                # El feed repite una licitación por cada modificación; nos quedamos con la más reciente.
                clave = rec.get("id") or rec.get("expediente")
                if not clave or clave in entradas_vistas:
                    descartes["repetida"] += 1
                    continue
                entradas_vistas.add(clave)

                upd = parse_iso(rec.get("actualizado"))
                if upd and upd < limite:
                    descartes["fuera del periodo"] += 1
                    continue

                salida, motivo = evaluar(rec, cfg, hoy)
                if salida is None:
                    descartes[motivo] += 1
                    continue
                if vistos_previos is not None and vistos_previos.get(clave) == rec.get("actualizado"):
                    descartes["ya entregada"] += 1
                    continue
                vistos[clave] = rec.get("actualizado")
                salida["fuente"] = "Plataforma de Contratación del Sector Público"
                salida["obtenidoEn"] = ahora.isoformat(timespec="seconds")
                lote.append(salida)
                if total + len(lote) >= max_resultados:
                    break

            if lote:
                await guardar(lote)
                total += len(lote)
            rango = (
                f"{min(fechas).isoformat(timespec='minutes')} a {max(fechas).isoformat(timespec='minutes')}"
                if fechas else "sin fechas"
            )
            resumen_descartes = ", ".join(f"{k}: {v}" for k, v in descartes.most_common()) or "ninguno"
            log(
                f"Página {paginas} de {nombre_feed}: {len(registros)} entradas ({rango}), "
                f"{len(lote)} coincidencias (total {total}). Descartes: {resumen_descartes}."
            )

            # Se para cuando TODA la página es anterior al periodo pedido (no se asume orden dentro de la página).
            if fechas and max(fechas) < limite:
                break
            url = siguiente
            if url:
                await asyncio.sleep(ESPERA_ENTRE_PAGINAS)

    return total, vistos


async def main() -> None:
    async with Actor:
        entrada = await Actor.get_input() or {}
        cfg = Config.desde_input(entrada)

        feeds = [FEED_LICITACIONES]
        if entrada.get("incluirContratosMenores", False):
            feeds.append(FEED_CONTRATOS_MENORES)

        solo_nuevas = entrada.get("soloNuevasDesdeUltimaEjecucion", False)
        almacen = None
        vistos_previos = None
        if solo_nuevas:
            almacen = await Actor.open_key_value_store(name="licitaciones-energia-estado")
            vistos_previos = await almacen.get_value(CLAVE_ESTADO) or {}

        async def guardar(lote: list[dict]) -> None:
            await Actor.push_data(lote)

        total, vistos = await recorrer(
            feeds,
            cfg,
            fetch=descargar,
            guardar=guardar,
            log=Actor.log.info,
            max_paginas=int(entrada.get("maxPaginas", 30)),
            dias_atras=int(entrada.get("diasAtras", 2)),
            max_resultados=int(entrada.get("maxResultados", 1000)),
            ahora=datetime.now(timezone.utc),
            vistos_previos=vistos_previos,
        )

        if almacen is not None:
            # Solo se conservan las de los últimos 60 días para que el estado no crezca sin límite.
            corte = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
            vistos = {k: v for k, v in vistos.items() if v and v >= corte[:10]}
            await almacen.set_value(CLAVE_ESTADO, vistos)

        mensaje = f"{total} licitaciones de energía encontradas."
        Actor.log.info(mensaje)
        await Actor.set_status_message(mensaje)
