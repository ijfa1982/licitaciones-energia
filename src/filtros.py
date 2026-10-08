"""Clasificación por sector energético y filtros de la búsqueda."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .catalogo import COMUNIDADES, EXCLUSIONES_TITULO, SECTORES


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar palabras clave."""
    t = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _contiene(texto_norm: str, palabra: str) -> bool:
    p = normalizar(palabra)
    if len(p) <= 4:  # palabras cortas (p. ej. "led") solo como palabra completa
        return re.search(rf"\b{re.escape(p)}\b", texto_norm) is not None
    return p in texto_norm


@dataclass
class Config:
    sectores: list[str] = field(default_factory=lambda: list(SECTORES))
    cpv_extra: list[str] = field(default_factory=list)
    palabras_extra: list[str] = field(default_factory=list)
    usar_palabras_clave: bool = True
    comunidades: list[str] = field(default_factory=list)
    estados: list[str] = field(default_factory=lambda: ["PUB"])
    excluir_vencidas: bool = True
    presupuesto_min: Optional[float] = None
    presupuesto_max: Optional[float] = None

    @classmethod
    def desde_input(cls, data: dict) -> "Config":
        sectores = [s for s in (data.get("sectores") or list(SECTORES)) if s in SECTORES]
        return cls(
            sectores=sectores or list(SECTORES),
            cpv_extra=[c.strip().rstrip("0") or c.strip() for c in data.get("cpvExtra") or [] if c.strip()],
            palabras_extra=[p for p in data.get("palabrasClaveExtra") or [] if p.strip()],
            usar_palabras_clave=data.get("usarPalabrasClave", True),
            comunidades=[c for c in data.get("comunidades") or [] if c in COMUNIDADES],
            estados=data.get("estados") or ["PUB"],
            excluir_vencidas=data.get("excluirVencidas", True),
            presupuesto_min=data.get("presupuestoMinimo"),
            presupuesto_max=data.get("presupuestoMaximo"),
        )


def _es_cpv_energetico(codigo: str, prefijos: list[str]) -> bool:
    return any(codigo.startswith(p) for p in prefijos)


def clasificar(rec: dict, cfg: Config) -> tuple[list[str], list[str]]:
    """Devuelve (sectores detectados, motivos) para un registro.

    Un código CPV energético solo cuenta si es el CPV principal (el primero) o si al menos la mitad
    de los CPV del contrato son energéticos. Así se descartan contratos de otra cosa que incluyen
    una partida menor de energía (limpieza con mantenimiento de frío, ferretería con lámparas...).
    """
    sectores: list[str] = []
    motivos: list[str] = []
    cpvs = rec.get("cpv") or []
    titulo_norm = normalizar(rec.get("titulo") or "")

    if any(_contiene(titulo_norm, p) for p in EXCLUSIONES_TITULO):
        return [], []

    todos_prefijos = [p for clave in cfg.sectores for p in SECTORES[clave]["cpv"]] + cfg.cpv_extra
    energeticos = [c for c in cpvs if _es_cpv_energetico(c, todos_prefijos)]
    cpv_valido = bool(cpvs) and (cpvs[0] in energeticos or len(energeticos) * 2 >= len(cpvs))

    for clave in cfg.sectores:
        sector = SECTORES[clave]
        cpv_hit = None
        if cpv_valido:
            cpv_hit = next((c for c in cpvs if _es_cpv_energetico(c, sector["cpv"])), None)
        if cpv_hit:
            sectores.append(clave)
            motivos.append(f"CPV {cpv_hit}")
            continue
        if cfg.usar_palabras_clave:
            palabra = next((p for p in sector["palabras"] if _contiene(titulo_norm, p)), None)
            if palabra:
                sectores.append(clave)
                motivos.append(f'título: "{palabra}"')

    cpv_extra = next((c for c in cpvs if _es_cpv_energetico(c, cfg.cpv_extra)), None) if cpv_valido else None
    if cpv_extra:
        sectores.append("cpv_personalizado")
        motivos.append(f"CPV {cpv_extra}")
    palabra_extra = next((p for p in cfg.palabras_extra if _contiene(titulo_norm, p)), None)
    if palabra_extra:
        sectores.append("palabra_personalizada")
        motivos.append(f'título: "{palabra_extra}"')

    return sectores, motivos


def dias_restantes(fecha_limite: Optional[str], hoy: date) -> Optional[int]:
    if not fecha_limite:
        return None
    try:
        return (date.fromisoformat(fecha_limite) - hoy).days
    except ValueError:
        return None


def evaluar(rec: dict, cfg: Config, hoy: date) -> tuple[Optional[dict], str]:
    """Aplica todos los filtros. Devuelve (registro enriquecido, "ok") o (None, motivo del descarte)."""
    if cfg.estados and rec.get("estado") not in cfg.estados:
        return None, f"estado {rec.get('estado')}"

    dias = dias_restantes(rec.get("fechaLimite"), hoy)
    if cfg.excluir_vencidas and dias is not None and dias < 0:
        return None, "plazo vencido"

    if cfg.comunidades:
        nuts = rec.get("codigoNuts") or ""
        if not any(nuts.startswith(c) for c in cfg.comunidades):
            return None, "otra comunidad"

    importe = rec.get("presupuestoSinIva") or rec.get("valorEstimado")
    if cfg.presupuesto_min is not None and (importe is None or importe < cfg.presupuesto_min):
        return None, "presupuesto bajo"
    if cfg.presupuesto_max is not None and importe is not None and importe > cfg.presupuesto_max:
        return None, "presupuesto alto"

    sectores, motivos = clasificar(rec, cfg)
    if not sectores:
        return None, "no es de energía"

    salida = dict(rec)
    salida["sectores"] = [SECTORES[s]["nombre"] if s in SECTORES else s for s in sectores]
    salida["motivoCoincidencia"] = motivos
    salida["diasRestantes"] = dias
    return salida, "ok"


def aceptar(rec: dict, cfg: Config, hoy: date) -> Optional[dict]:
    """Igual que evaluar(), devolviendo solo el registro o None."""
    return evaluar(rec, cfg, hoy)[0]
