"""Actor de Apify: licitaciones públicas del sector energético en España (PLACSP)."""
from __future__ import annotations

import asyncio
import gzip
import math
import os
import time
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
MARGEN_SEGUNDOS = 45  # tiempo reservado para guardar el estado y terminar ordenadamente
EVENTO_RESULTADO = "apify-default-dataset-item"  # evento de pago por cada licitación entregada


def segundos_hasta_timeout() -> Optional[float]:
    """Segundos que quedan antes de que Apify corte la ejecución (None si no hay límite conocido)."""
    valor = os.environ.get("ACTOR_TIMEOUT_AT") or os.environ.get("APIFY_TIMEOUT_AT")
    fin = parse_iso(valor) if valor else None
    if fin is None:
        return None
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=timezone.utc)
    return (fin - datetime.now(timezone.utc)).total_seconds()


def cupo_de_pago() -> Optional[int]:
    """Licitaciones que aún caben en el gasto máximo que el cliente fijó para esta ejecución.

    None si no hay límite o el SDK no lo puede calcular (por ejemplo, al probar en local).
    """
    try:
        n = Actor.get_charging_manager().calculate_max_event_charge_count_within_limit(EVENTO_RESULTADO)
    except Exception:  # noqa: BLE001
        return None
    if n is None or (isinstance(n, float) and math.isinf(n)):
        return None
    return max(int(n), 0)


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
    segundos_restantes: Callable[[], Optional[float]] = lambda: None,
    cupo_restante: Callable[[], Optional[int]] = lambda: None,
) -> tuple[int, dict]:
    """Recorre las páginas de cada feed (de más reciente a más antigua) y guarda las coincidencias.

    Devuelve (número de resultados guardados, mapa expediente -> fecha de actualización vista).
    """
    hoy = ahora.astimezone(MADRID).date()
    entradas_vistas: set[str] = set()
    vistos: dict = dict(vistos_previos or {})
    total = 0
    sin_tiempo = False
    sin_cupo = False
    duracion_pagina = 30.0  # estimación inicial; se ajusta con la última página leída

    for feed in feeds:
        if sin_tiempo or sin_cupo:
            break
        url: Optional[str] = feed
        paginas = 0
        nombre_feed = feed.rsplit("/", 1)[-1]
        limite = ahora - timedelta(days=dias_atras)
        while url and paginas < max_paginas and total < max_resultados:
            if not url_oficial(url):
                log(f"URL descartada por no ser de la Plataforma oficial: {url}")
                break
            restantes = segundos_restantes()
            if restantes is not None and restantes < MARGEN_SEGUNDOS + duracion_pagina:
                log(
                    f"Se acerca el límite de tiempo de la ejecución (quedan {restantes:.0f} s): "
                    f"se termina con {total} resultados. Para revisar más días, aumenta el tiempo "
                    f"máximo (Timeout) en las opciones de ejecución."
                )
                sin_tiempo = True
                break
            inicio_pagina = time.monotonic()
            datos = await fetch(url)
            registros, siguiente, _ = parse_feed(datos)
            paginas += 1
            duracion_pagina = time.monotonic() - inicio_pagina
            fechas = [d for d in (parse_iso(r.get("actualizado")) for r in registros) if d]

            if paginas == 1 and registros:
                for r in registros[:3]:
                    log(
                        "Muestra: "
                        f"estado={r.get('estado')} actualizado={r.get('actualizado')} "
                        f"fechaLimite={r.get('fechaLimite')} cpv={r.get('cpv')} "
                        f"titulo={(r.get('titulo') or '')[:80]!r}"
                    )
                if fechas:
                    # La Plataforma publica el feed con retraso (a veces varios días): el periodo pedido
                    # se cuenta desde la última actualización publicada, no desde hoy.
                    ultima = max(fechas)
                    if ultima < ahora:
                        limite = ultima - timedelta(days=dias_atras)
                    retraso_horas = (ahora - ultima).total_seconds() / 3600
                    if retraso_horas > 24:
                        log(
                            f"Aviso: la última actualización publicada en el feed es del "
                            f"{ultima.isoformat(timespec='minutes')} ({retraso_horas / 24:.1f} días de retraso). "
                            f"Se revisan los {dias_atras} días anteriores a esa fecha."
                        )
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
                salida["_clave"] = clave
                salida["fuente"] = "Plataforma de Contratación del Sector Público"
                salida["obtenidoEn"] = ahora.isoformat(timespec="seconds")
                lote.append(salida)
                if total + len(lote) >= max_resultados:
                    break

            cupo = cupo_restante()
            if cupo is not None and len(lote) > cupo:
                # No se entregan (ni se cobran) más licitaciones de las que permite el gasto máximo del cliente.
                for rec in lote[cupo:]:
                    clave = rec.get("expediente")
                    vistos.pop(rec.pop("_clave", clave), None)
                lote = lote[:cupo]
                sin_cupo = True
            for rec in lote:
                rec.pop("_clave", None)
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

            if sin_cupo or (cupo_restante() == 0):
                log(
                    f"Se ha alcanzado el gasto máximo por ejecución que has fijado: se termina con "
                    f"{total} resultados. Para recibir más, sube el límite (Max charge) en las opciones."
                )
                sin_cupo = True
                break

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
            segundos_restantes=segundos_hasta_timeout,
            cupo_restante=cupo_de_pago,
        )

        if almacen is not None:
            # Solo se conservan las de los últimos 60 días para que el estado no crezca sin límite.
            corte = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
            vistos = {k: v for k, v in vistos.items() if v and v >= corte[:10]}
            await almacen.set_value(CLAVE_ESTADO, vistos)

        mensaje = f"{total} licitaciones de energía encontradas."
        Actor.log.info(mensaje)
        await Actor.set_status_message(mensaje)
