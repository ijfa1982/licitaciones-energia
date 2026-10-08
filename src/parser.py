"""Lectura del feed ATOM/CODICE de la Plataforma de Contratación del Sector Público.

Se compara por nombre local de etiqueta (sin espacio de nombres), para que un cambio
de prefijos o de URI de namespace en el feed no rompa la extracción.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import fromstring

from .catalogo import COMUNIDADES, ESTADOS, PROCEDIMIENTOS, TIPOS_CONTRATO


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _child(el: Optional[Element], name: str) -> Optional[Element]:
    if el is None:
        return None
    for c in el:
        if _local(c.tag) == name:
            return c
    return None


def _children(el: Optional[Element], name: str) -> list[Element]:
    if el is None:
        return []
    return [c for c in el if _local(c.tag) == name]


def _path(el: Optional[Element], *names: str) -> Optional[Element]:
    for n in names:
        el = _child(el, n)
        if el is None:
            return None
    return el


def _descendants(el: Optional[Element], name: str) -> Iterable[Element]:
    if el is None:
        return []
    return (d for d in el.iter() if _local(d.tag) == name)


def _text(el: Optional[Element]) -> Optional[str]:
    if el is None or el.text is None:
        return None
    t = el.text.strip()
    return t or None


def _amount(el: Optional[Element]) -> Optional[float]:
    t = _text(el)
    if t is None:
        return None
    try:
        return round(float(t), 2)
    except ValueError:
        return None


def _date(value: Optional[str]) -> Optional[str]:
    """'2026-10-20' o '2026-10-20+02:00' -> '2026-10-20'."""
    if not value:
        return None
    return value[:10] if len(value) >= 10 else None


def _time(value: Optional[str]) -> Optional[str]:
    """'23:59:00' o '23:59:00+02:00' -> '23:59'."""
    if not value:
        return None
    return value[:5] if len(value) >= 5 else None


def _parent_names(lcp: Optional[Element]) -> list[str]:
    """Cadena de órganos superiores (de más cercano a más general)."""
    names: list[str] = []
    node = _child(lcp, "ParentLocatedParty")
    while node is not None and len(names) < 10:
        n = _text(_path(node, "PartyName", "Name"))
        if n:
            names.append(n)
        node = _child(node, "ParentLocatedParty")
    return names


def _documents(cfs: Optional[Element]) -> list[dict]:
    docs = []
    kinds = {
        "LegalDocumentReference": "Pliego administrativo",
        "TechnicalDocumentReference": "Pliego técnico",
        "AdditionalDocumentReference": "Documento adicional",
    }
    for tag, label in kinds.items():
        for ref in _children(cfs, tag):
            uri = _text(_path(ref, "Attachment", "ExternalReference", "URI"))
            if uri:
                docs.append({"tipo": label, "nombre": _text(_child(ref, "ID")), "url": uri})
    return docs


def parse_entry(entry: Element) -> Optional[dict]:
    """Convierte un <entry> en un registro plano. Devuelve None si no es una licitación."""
    cfs = _child(entry, "ContractFolderStatus")
    if cfs is None:
        return None

    link = _child(entry, "link")
    lcp = _child(cfs, "LocatedContractingParty")
    party = _child(lcp, "Party")
    pp = _child(cfs, "ProcurementProject")
    budget = _child(pp, "BudgetAmount")
    location = _child(pp, "RealizedLocation")
    tp = _child(cfs, "TenderingProcess")
    deadline = _child(tp, "TenderSubmissionDeadlinePeriod")

    nif = None
    for pid in _children(party, "PartyIdentification"):
        id_el = _child(pid, "ID")
        if id_el is not None and (id_el.get("schemeName") or "").upper() == "NIF":
            nif = _text(id_el)

    cpvs: list[str] = []
    for code in _descendants(cfs, "ItemClassificationCode"):
        c = _text(code)
        if c and c not in cpvs:
            cpvs.append(c)

    nuts = _text(_child(location, "CountrySubentityCode"))
    comunidad = COMUNIDADES.get(nuts[:4]) if nuts and len(nuts) >= 4 else None

    status = _text(_child(cfs, "ContractFolderStatusCode"))
    type_code = _text(_child(pp, "TypeCode"))
    proc_code = _text(_child(tp, "ProcedureCode"))
    duration = _child(_child(pp, "PlannedPeriod"), "DurationMeasure")

    result = _child(cfs, "TenderResult")
    winner = _text(_path(result, "WinningParty", "PartyName", "Name"))
    awarded = _amount(_path(result, "AwardedTenderedProject", "LegalMonetaryTotal", "TaxExclusiveAmount"))

    end_date = _date(_text(_child(deadline, "EndDate")))
    end_time = _time(_text(_child(deadline, "EndTime")))

    return {
        "id": _text(_child(entry, "id")),
        "expediente": _text(_child(cfs, "ContractFolderID")),
        "titulo": _text(_child(pp, "Name")) or _text(_child(entry, "title")),
        "estado": status,
        "estadoTexto": ESTADOS.get(status or "", status),
        "organoContratacion": _text(_path(party, "PartyName", "Name")),
        "organoNif": nif,
        "organosSuperiores": _parent_names(lcp),
        "organoCiudad": _text(_path(party, "PostalAddress", "CityName")),
        "tipoContrato": TIPOS_CONTRATO.get(type_code or "", type_code),
        "procedimiento": PROCEDIMIENTOS.get(proc_code or "", proc_code),
        "cpv": cpvs,
        "presupuestoSinIva": _amount(_child(budget, "TaxExclusiveAmount")),
        "presupuestoConIva": _amount(_child(budget, "TotalAmount")),
        "valorEstimado": _amount(_child(budget, "EstimatedOverallContractAmount")),
        "lugarEjecucion": _text(_child(location, "CountrySubentity")),
        "codigoNuts": nuts,
        "comunidadAutonoma": comunidad,
        "municipio": _text(_path(location, "Address", "CityName")),
        "duracion": (
            f"{_text(duration)} {duration.get('unitCode', '')}".strip() if _text(duration) else None
        ),
        "fechaLimite": end_date,
        "horaLimite": end_time,
        "numeroLotes": len(_children(cfs, "ProcurementProjectLot")) or None,
        "adjudicatario": winner,
        "importeAdjudicacion": awarded,
        "documentos": _documents(cfs),
        "urlDetalle": link.get("href") if link is not None else None,
        "actualizado": _text(_child(entry, "updated")),
    }


def parse_feed(xml_bytes: bytes) -> tuple[list[dict], Optional[str], Optional[str]]:
    """Devuelve (registros, url de la página siguiente, fecha de actualización más antigua)."""
    root = fromstring(xml_bytes)
    next_url = None
    for link in _children(root, "link"):
        if link.get("rel") == "next":
            next_url = link.get("href")

    records: list[dict] = []
    oldest: Optional[str] = None
    for entry in _children(root, "entry"):
        upd = _text(_child(entry, "updated"))
        if upd and (oldest is None or upd < oldest):
            oldest = upd
        rec = parse_entry(entry)
        if rec is not None:
            records.append(rec)
    return records, next_url, oldest


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
