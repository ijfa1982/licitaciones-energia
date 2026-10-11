import asyncio
import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests", "fake_apify"))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import muestra  # noqa: E402
from src import main as actor_main  # noqa: E402
from web import enviar_alertas, generar_datos  # noqa: E402

AHORA = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)
HOY = date(2026, 10, 8)


async def fetch_falso(url):
    return muestra.PAGINAS[url]


class TestWeb(unittest.TestCase):
    def setUp(self):
        actor_main.ESPERA_ENTRE_PAGINAS = 0
        generar_datos.descargar = fetch_falso

    def leer(self):
        return asyncio.run(generar_datos.leer_feed(2, AHORA, log=lambda *_: None))

    def test_combinar_y_ranking(self):
        nuevos = self.leer()
        self.assertTrue(nuevos)
        abiertas, adj, nuevas_hoy = generar_datos.combinar({}, nuevos, HOY)
        self.assertTrue(all(r["estado"] in ("PUB", "PRE") for r in abiertas))
        self.assertEqual(len(nuevas_hoy), len(abiertas))
        # Segunda pasada con los mismos datos: nada es nuevo.
        previos = {"abiertas": abiertas, "adjudicaciones": adj}
        ab2, adj2, nuevas2 = generar_datos.combinar(previos, nuevos, HOY)
        self.assertEqual(nuevas2, [])
        self.assertEqual(len(ab2), len(abiertas))
        rank = generar_datos.ranking(adj)
        if adj:
            self.assertGreaterEqual(rank[0]["contratos"], 1)

    def test_vencidas_salen(self):
        previos = {"abiertas": [{"id": "x", "titulo": "Vieja", "estado": "PUB", "fechaLimite": "2026-01-01"}]}
        ab, _, _ = generar_datos.combinar(previos, [], HOY)
        self.assertEqual(ab, [])

    def test_adjudicada_sale_de_abiertas(self):
        previos = {"abiertas": [{"id": "x", "titulo": "A", "estado": "PUB", "fechaLimite": "2026-12-01"}]}
        rec = {"id": "x", "titulo": "A", "estado": "ADJ", "actualizado": "2026-10-07T10:00:00+02:00",
               "adjudicatarios": [{"nombre": "Solar SL", "nif": "B12345678", "importeSinIva": 1000}]}
        ab, adj, _ = generar_datos.combinar(previos, [rec], HOY)
        self.assertEqual(ab, [])
        self.assertEqual(adj[0]["adjudicatarios"][0]["nombre"], "Solar SL")
        self.assertEqual(generar_datos.ranking(adj)[0]["nif"], "B12345678")

    def test_main_escribe_ficheros(self):
        with tempfile.TemporaryDirectory() as d:
            sal, priv = os.path.join(d, "site"), os.path.join(d, "priv")
            argv = sys.argv
            sys.argv = ["x", "--salida", sal, "--privado", priv]
            real_now = generar_datos.datetime
            try:
                class Fijo(real_now):
                    @classmethod
                    def now(cls, tz=None):
                        return AHORA
                generar_datos.datetime = Fijo
                generar_datos.main()
            finally:
                sys.argv = argv
                generar_datos.datetime = real_now
            web = json.load(open(os.path.join(sal, "web.json"), encoding="utf-8"))
            self.assertIn("abiertas", web)
            self.assertLessEqual(len(web["ranking"]), 10)
            self.assertTrue(os.path.exists(os.path.join(priv, "ranking_completo.json")))
            self.assertFalse(os.path.exists(os.path.join(sal, "ranking_completo.json")))

    def test_filtrar_alertas(self):
        lic = [
            {"titulo": "Instalación fotovoltaica en colegio", "sectores": ["Fotovoltaica y autoconsumo"],
             "comunidadAutonoma": "Comunidad de Madrid", "presupuestoSinIva": 50000},
            {"titulo": "Alumbrado LED", "sectores": ["Alumbrado público e iluminación"],
             "comunidadAutonoma": "Andalucía", "presupuestoSinIva": 10000},
        ]
        s = {"sectores": ["Fotovoltaica y autoconsumo"], "comunidades": ["Comunidad de Madrid"],
             "presupuestoMinimo": 20000, "palabras": ["colegio"]}
        self.assertEqual(len(enviar_alertas.filtrar(lic, s)), 1)
        self.assertEqual(len(enviar_alertas.filtrar(lic, {})), 2)
        self.assertEqual(enviar_alertas.filtrar(lic, {"presupuestoMinimo": 60000}), [])
        csv = enviar_alertas.ranking_csv([{"nombre": "A", "nif": "B1", "contratos": 2, "importe": 10.5,
                                           "comunidades": ["Madrid"], "sectores": ["Alumbrado"]}])
        self.assertIn("10,5".encode(), csv)


if __name__ == "__main__":
    unittest.main()


class TestFotos(unittest.TestCase):
    def test_extraer_creditos(self):
        from web import fotos
        datos = {"query": {"pages": {"1": {"imageinfo": [{
            "thumburl": "https://upload.wikimedia.org/x/1600px-a.jpg", "descriptionurl": "https://commons.wikimedia.org/wiki/File:A.jpg",
            "extmetadata": {"Artist": {"value": '<a href="u">Ana &amp; Luis</a>'}, "LicenseShortName": {"value": "CC BY-SA 4.0"}}}]}}}}
        m = fotos.extraer(datos)
        self.assertEqual(m["autor"], "Ana & Luis")
        self.assertEqual(m["licencia"], "CC BY-SA 4.0")
        self.assertIsNone(fotos.extraer({"query": {"pages": {"-1": {"missing": ""}}}}))


def _topo(objeto, geometrias):
    """TopoJSON mínimo sin cuantizar: un arco cerrado por geometría."""
    arcos, geoms = [], []
    for gid, anillo in geometrias:
        arcos.append(anillo + [anillo[0]])
        geoms.append({"type": "Polygon", "id": gid, "arcs": [[len(arcos) - 1]]})
    return {"type": "Topology", "arcs": arcos, "objects": {objeto: {"type": "GeometryCollection", "geometries": geoms}}}


class TestMapa(unittest.TestCase):
    def test_construir(self):
        from web import mapa
        madrid = [(-4.2, 40.0), (-3.0, 40.0), (-3.0, 41.0), (-4.2, 41.0)]
        andalucia = [(-7.0, 36.0), (-2.0, 36.0), (-2.0, 38.5), (-7.0, 38.5)]
        canarias = [(-18.0, 27.6), (-13.4, 27.6), (-13.4, 29.4), (-18.0, 29.4)]
        ccaa = _topo("autonomous_regions", [("13", madrid), ("01", andalucia), ("05", canarias)])
        prov = _topo("provinces", [("28", madrid), ("41", andalucia), ("35", canarias)])
        m = mapa.construir(ccaa, prov)
        nombres = {c["nombre"] for c in m["comunidades"]}
        self.assertEqual(nombres, {"Comunidad de Madrid", "Andalucía", "Canarias"})
        self.assertEqual(m["ancho"], 1000)
        self.assertTrue(m["comunidades"][0]["d"].startswith("M"))
        p = {x["nombre"]: x for x in m["provincias"]}
        self.assertEqual(p["Sevilla"]["comunidad"], "Andalucía")
        self.assertIsNotNone(m["recuadroCanarias"])
        # El centro de Madrid cae dentro de su caja en el dibujo
        madrid_svg = next(c for c in m["comunidades"] if c["nombre"] == "Comunidad de Madrid")
        xs = [float(v.split(",")[0]) for v in madrid_svg["d"][1:-1].split("L")]
        self.assertTrue(min(xs) <= madrid_svg["c"][0] <= max(xs))

    def test_cuantizado(self):
        from web import mapa
        topo = {"transform": {"scale": [0.5, 0.5], "translate": [10, 20]}, "arcs": [[[0, 0], [2, 0], [0, 2]]]}
        self.assertEqual(mapa.decodificar_arcos(topo)[0], [(10, 20), (11, 20), (11, 21)])
