"""Genera el mapa de España (comunidades y provincias) que usa la web, en coordenadas de dibujo SVG.

Descarga los contornos oficiales simplificados del paquete es-atlas (datos del IGN/INE en TopoJSON),
los proyecta y guarda en web/site/data/mapa.json una ruta SVG por comunidad y por provincia, con el
punto donde poner la cifra. Canarias se coloca en un recuadro abajo a la izquierda, como en los mapas
oficiales. Se ejecuta en GitHub Actions antes de publicar; si falla, la web muestra el mapa de casillas.
"""
from __future__ import annotations

import json
import math
import os
import sys
import urllib.request

FUENTES = [
    "https://cdn.jsdelivr.net/npm/es-atlas@0.6.0/es/{}.json",
    "https://unpkg.com/es-atlas@0.6.0/es/{}.json",
    "https://cdn.jsdelivr.net/npm/es-atlas/es/{}.json",
]
ANCHO = 1000

# Códigos INE: comunidad (01-19) y provincia (01-52), con los nombres que usan los datos de la web.
COMUNIDADES_INE = {
    "01": "Andalucía", "02": "Aragón", "03": "Principado de Asturias", "04": "Illes Balears", "05": "Canarias",
    "06": "Cantabria", "07": "Castilla y León", "08": "Castilla-La Mancha", "09": "Cataluña",
    "10": "Comunitat Valenciana", "11": "Extremadura", "12": "Galicia", "13": "Comunidad de Madrid",
    "14": "Región de Murcia", "15": "Comunidad Foral de Navarra", "16": "País Vasco", "17": "La Rioja",
    "18": "Ceuta", "19": "Melilla",
}
PROVINCIAS_INE = {
    "01": ("Araba/Álava", "16"), "02": ("Albacete", "08"), "03": ("Alicante/Alacant", "10"), "04": ("Almería", "01"),
    "05": ("Ávila", "07"), "06": ("Badajoz", "11"), "07": ("Illes Balears", "04"), "08": ("Barcelona", "09"),
    "09": ("Burgos", "07"), "10": ("Cáceres", "11"), "11": ("Cádiz", "01"), "12": ("Castellón/Castelló", "10"),
    "13": ("Ciudad Real", "08"), "14": ("Córdoba", "01"), "15": ("A Coruña", "12"), "16": ("Cuenca", "08"),
    "17": ("Girona", "09"), "18": ("Granada", "01"), "19": ("Guadalajara", "08"), "20": ("Gipuzkoa", "16"),
    "21": ("Huelva", "01"), "22": ("Huesca", "02"), "23": ("Jaén", "01"), "24": ("León", "07"),
    "25": ("Lleida", "09"), "26": ("La Rioja", "17"), "27": ("Lugo", "12"), "28": ("Madrid", "13"),
    "29": ("Málaga", "01"), "30": ("Murcia", "14"), "31": ("Navarra", "15"), "32": ("Ourense", "12"),
    "33": ("Asturias", "03"), "34": ("Palencia", "07"), "35": ("Las Palmas", "05"), "36": ("Pontevedra", "12"),
    "37": ("Salamanca", "07"), "38": ("Santa Cruz de Tenerife", "05"), "39": ("Cantabria", "06"),
    "40": ("Segovia", "07"), "41": ("Sevilla", "01"), "42": ("Soria", "07"), "43": ("Tarragona", "09"),
    "44": ("Teruel", "02"), "45": ("Toledo", "08"), "46": ("Valencia/València", "10"), "47": ("Valladolid", "07"),
    "48": ("Bizkaia", "16"), "49": ("Zamora", "07"), "50": ("Zaragoza", "02"), "51": ("Ceuta", "18"),
    "52": ("Melilla", "19"),
}


# --- TopoJSON a polígonos -------------------------------------------------------------------------

def decodificar_arcos(topo: dict) -> list[list[tuple[float, float]]]:
    t = topo.get("transform")
    arcos = []
    for arco in topo["arcs"]:
        if t:
            x = y = 0
            puntos = []
            for dx, dy, *_ in arco:
                x += dx
                y += dy
                puntos.append((x * t["scale"][0] + t["translate"][0], y * t["scale"][1] + t["translate"][1]))
        else:
            puntos = [(p[0], p[1]) for p in arco]
        arcos.append(puntos)
    return arcos


def _anillo(indices: list[int], arcos) -> list[tuple[float, float]]:
    puntos: list[tuple[float, float]] = []
    for i in indices:
        tramo = arcos[i] if i >= 0 else list(reversed(arcos[~i]))
        puntos.extend(tramo if not puntos else tramo[1:])
    return puntos


def poligonos(geom: dict, arcos) -> list[list[list[tuple[float, float]]]]:
    if geom.get("type") == "Polygon":
        return [[_anillo(r, arcos) for r in geom["arcs"]]]
    if geom.get("type") == "MultiPolygon":
        return [[_anillo(r, arcos) for r in p] for p in geom["arcs"]]
    return []


def objeto(topo: dict, pistas: tuple[str, ...]) -> list[dict]:
    for nombre, obj in topo.get("objects", {}).items():
        if any(p in nombre.lower() for p in pistas):
            return obj.get("geometries", [])
    return []


# --- Proyección ---------------------------------------------------------------------------------

def es_geografico(polis) -> bool:
    return all(-30 <= x <= 10 and 20 <= y <= 50 for p in polis for anillo in p for x, y in anillo[:5])


def proyectar_lonlat(lon: float, lat: float) -> tuple[float, float]:
    # Equirrectangular corregida en latitud 40°: suficiente para un país del tamaño de España.
    if lon < -12:  # Canarias, desplazada al recuadro de abajo a la izquierda
        lon, lat = lon + 6.5, lat + 7.2
    return (lon * math.cos(math.radians(40)), -lat)


def _area_centroide(anillo):
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:] + anillo[:1]):
        f = x1 * y2 - x2 * y1
        a += f
        cx += (x1 + x2) * f
        cy += (y1 + y2) * f
    if abs(a) < 1e-12:
        xs, ys = zip(*anillo)
        return 0.0, (sum(xs) / len(xs), sum(ys) / len(ys))
    return abs(a / 2), (cx / (3 * a), cy / (3 * a))


def construir(topo_ccaa: dict, topo_prov: dict) -> dict:
    capas = {}
    for clave, topo, pistas in (("comunidades", topo_ccaa, ("autonom", "ccaa", "comunidad")),
                                ("provincias", topo_prov, ("provinc",))):
        arcos = decodificar_arcos(topo)
        capas[clave] = [(g, poligonos(g, arcos)) for g in objeto(topo, pistas)]
    todas = [p for capa in capas.values() for _, ps in capa for p in ps]
    geo = es_geografico(todas)
    proy = (lambda x, y: proyectar_lonlat(x, y)) if geo else (lambda x, y: (x, y))

    puntos = [proy(x, y) for p in todas for anillo in p for x, y in anillo]
    xs, ys = zip(*puntos)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    escala = ANCHO / (maxx - minx)
    alto = (maxy - miny) * escala

    def a_svg(x, y):
        px, py = proy(x, y)
        return ((px - minx) * escala, (py - miny) * escala)

    def ruta_y_centro(polis):
        trozos, mejor = [], (0.0, (0.0, 0.0))
        for p in polis:
            for i, anillo in enumerate(p):
                pts = [a_svg(x, y) for x, y in anillo]
                if len(pts) < 3:
                    continue
                trozos.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
                if i == 0:
                    area, c = _area_centroide(pts)
                    if area > mejor[0]:
                        mejor = (area, c)
        return "".join(trozos), [round(mejor[1][0], 1), round(mejor[1][1], 1)]

    def nombre_comunidad(g):
        cod = str(g.get("id", "")).zfill(2)
        return COMUNIDADES_INE.get(cod) or (g.get("properties") or {}).get("name", "")

    salida = {"ancho": ANCHO, "alto": round(alto, 1), "comunidades": [], "provincias": [],
              "recuadroCanarias": None}
    for g, polis in capas["comunidades"]:
        d, c = ruta_y_centro(polis)
        salida["comunidades"].append({"nombre": nombre_comunidad(g), "d": d, "c": c})
    for g, polis in capas["provincias"]:
        cod = str(g.get("id", "")).zfill(2)
        nombre, ca = PROVINCIAS_INE.get(cod, ((g.get("properties") or {}).get("name", ""), ""))
        d, c = ruta_y_centro(polis)
        salida["provincias"].append({"nombre": nombre, "comunidad": COMUNIDADES_INE.get(ca, ""), "d": d, "c": c})
    if geo:
        # Recuadro de Canarias: caja alrededor de sus puntos proyectados
        can = [a_svg(x, y) for g, ps in capas["comunidades"] if nombre_comunidad(g) == "Canarias"
               for p in ps for anillo in p for x, y in anillo]
        if can:
            cx, cy = zip(*can)
            m = 12
            salida["recuadroCanarias"] = [round(min(cx) - m, 1), round(min(cy) - m, 1),
                                          round(max(cx) - min(cx) + 2 * m, 1), round(max(cy) - min(cy) + 2 * m, 1)]
    return salida


def descargar(nombre: str) -> dict:
    error = None
    for f in FUENTES:
        try:
            req = urllib.request.Request(f.format(nombre), headers={"User-Agent": "LicitacionesEnergia/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            error = e
    raise RuntimeError(f"No se pudo descargar {nombre}: {error}")


def main(salida: str = "web/site/data/mapa.json") -> None:
    try:
        mapa = construir(descargar("autonomous_regions"), descargar("provinces"))
    except Exception as e:  # noqa: BLE001 - sin mapa la web usa las casillas
        print(f"Mapa no generado: {e}", file=sys.stderr)
        return
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(mapa, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Mapa: {len(mapa['comunidades'])} comunidades, {len(mapa['provincias'])} provincias, "
          f"{os.path.getsize(salida) // 1024} KB")


if __name__ == "__main__":
    main(*sys.argv[1:])
