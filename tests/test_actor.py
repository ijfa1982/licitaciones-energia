import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests", "fake_apify"))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import muestra  # noqa: E402
from src import main as actor_main  # noqa: E402
from src.filtros import Config, aceptar, normalizar  # noqa: E402
from src.parser import parse_feed  # noqa: E402

AHORA = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)


async def fetch_falso(url):
    return muestra.PAGINAS[url]


def ejecutar(cfg, **kw):
    guardados = []
    logs = []

    async def guardar(lote):
        guardados.extend(lote)

    actor_main.ESPERA_ENTRE_PAGINAS = 0
    total, vistos = asyncio.run(
        actor_main.recorrer(
            [actor_main.FEED_LICITACIONES], cfg, fetch=fetch_falso, guardar=guardar, log=logs.append,
            max_paginas=kw.get("max_paginas", 10), dias_atras=kw.get("dias_atras", 2),
            max_resultados=kw.get("max_resultados", 1000), ahora=AHORA,
            vistos_previos=kw.get("vistos_previos"),
        )
    )
    return guardados, total, vistos, logs


class TestParser(unittest.TestCase):
    def test_campos(self):
        regs, sig, antigua = parse_feed(muestra.PAGINA_1)
        self.assertEqual(len(regs), 6)
        self.assertEqual(sig, muestra.URL_PAG2)
        self.assertEqual(antigua, "2026-10-08T07:00:00.000+02:00")
        r = regs[0]
        self.assertEqual(r["expediente"], "EXP-1")
        self.assertEqual(r["estado"], "PUB")
        self.assertEqual(r["estadoTexto"], "En plazo")
        self.assertEqual(r["organoContratacion"], "Ayuntamiento de Ejemplo")
        self.assertEqual(r["organoNif"], "P0801900B")
        self.assertEqual(r["organosSuperiores"], ["ENTIDADES LOCALES", "Cataluña"])
        self.assertEqual(r["cpv"], ["09331200", "45261215"])
        self.assertEqual(r["presupuestoSinIva"], 150000.0)
        self.assertEqual(r["presupuestoConIva"], 181500.0)
        self.assertEqual(r["comunidadAutonoma"], "Cataluña")
        self.assertEqual(r["tipoContrato"], "Suministros")
        self.assertEqual(r["procedimiento"], "Abierto")
        self.assertEqual(r["fechaLimite"], "2026-10-30")
        self.assertEqual(r["horaLimite"], "14:00")
        self.assertEqual(r["duracion"], "6 MON")
        self.assertEqual(r["documentos"][0]["tipo"], "Pliego administrativo")
        self.assertIn("idEvl=1", r["urlDetalle"])

    def test_adjudicacion(self):
        regs, _, _ = parse_feed(muestra.PAGINA_1)
        r = regs[3]
        self.assertEqual(r["adjudicatario"], "Solar Ejemplo SL")
        self.assertEqual(r["importeAdjudicacion"], 120000.0)


class TestFiltros(unittest.TestCase):
    def test_normalizar(self):
        self.assertEqual(normalizar("Eficiencia Energética"), "eficiencia energetica")

    def test_led_palabra_completa(self):
        cfg = Config()
        hoy = AHORA.date()
        base = {"estado": "PUB", "cpv": ["79000000"], "fechaLimite": "2026-11-01"}
        self.assertIsNotNone(aceptar({**base, "titulo": "Luminarias LED para el parque"}, cfg, hoy))
        self.assertIsNone(aceptar({**base, "titulo": "Servicio de ledger contable"}, cfg, hoy))

    def test_presupuesto(self):
        cfg = Config(presupuesto_max=100000)
        rec = {"estado": "PUB", "cpv": ["09331200"], "titulo": "x", "presupuestoSinIva": 150000}
        self.assertIsNone(aceptar(rec, cfg, AHORA.date()))


class TestRecorrido(unittest.TestCase):
    def test_por_defecto(self):
        guardados, total, _, _ = ejecutar(Config())
        expedientes = [g["expediente"] for g in guardados]
        # 1 FV (CPV), 2 alumbrado (palabra), 6 suministro, 7 recarga (palabra + CPV 4531)
        self.assertEqual(expedientes, ["EXP-1", "EXP-2", "EXP-6", "EXP-7"])
        self.assertEqual(total, 4)
        fv = guardados[0]
        self.assertIn("Fotovoltaica y autoconsumo", fv["sectores"])
        self.assertEqual(fv["diasRestantes"], 22)
        self.assertEqual(guardados[0]["titulo"], "Suministro e instalación de planta fotovoltaica para autoconsumo en el polideportivo")
        alumbrado = guardados[1]
        self.assertEqual(alumbrado["sectores"], ["Alumbrado público e iluminación"])
        self.assertTrue(alumbrado["motivoCoincidencia"][0].startswith("título"))

    def test_no_baja_a_paginas_antiguas(self):
        _, _, _, logs = ejecutar(Config(), dias_atras=2)
        paginas = [l for l in logs if l.startswith("Página")]
        # La página 3 es entera de septiembre: se lee, se descarta y ya no se sigue.
        self.assertEqual(len(paginas), 3)
        self.assertIn("fuera del periodo: 1", paginas[2])
        self.assertTrue(any(l.startswith("Muestra:") for l in logs))

    def test_para_si_toda_la_pagina_es_antigua(self):
        # Con 1 día hacia atrás el límite es el 7/10 a las 09:00 UTC y toda la página 2 es anterior:
        # se lee, se descarta y no se baja a la 3.
        _, _, _, logs = ejecutar(Config(), dias_atras=1)
        paginas = [l for l in logs if l.startswith("Página")]
        self.assertEqual(len(paginas), 2)

    def test_resumen_descartes(self):
        _, _, _, logs = ejecutar(Config())
        primera = next(l for l in logs if l.startswith("Página 1"))
        self.assertIn("no es de energía: 1", primera)
        self.assertIn("estado ADJ: 1", primera)
        self.assertIn("plazo vencido: 1", primera)

    def test_comunidad_y_sector(self):
        guardados, _, _, _ = ejecutar(Config(comunidades=["ES52"], sectores=["movilidad_electrica"]))
        self.assertEqual([g["expediente"] for g in guardados], ["EXP-7"])

    def test_adjudicadas(self):
        guardados, _, _, _ = ejecutar(Config(estados=["ADJ"]))
        self.assertEqual([g["expediente"] for g in guardados], ["EXP-4"])

    def test_vencidas(self):
        guardados, _, _, _ = ejecutar(Config(excluir_vencidas=False))
        self.assertIn("EXP-5", [g["expediente"] for g in guardados])

    def test_max_resultados(self):
        guardados, total, _, _ = ejecutar(Config(), max_resultados=2)
        self.assertEqual(total, 2)
        self.assertEqual(len(guardados), 2)

    def test_solo_nuevas(self):
        _, _, vistos, _ = ejecutar(Config(), vistos_previos={})
        guardados, total, _, _ = ejecutar(Config(), vistos_previos=vistos)
        self.assertEqual(total, 0)
        self.assertEqual(guardados, [])

    def test_url_no_oficial(self):
        self.assertFalse(actor_main.url_oficial("https://ejemplo.com/feed.atom"))
        self.assertTrue(actor_main.url_oficial(muestra.URL_PAG2))


class TestMain(unittest.TestCase):
    def test_main_completo(self):
        from apify import Actor

        Actor.input = {"sectores": ["fotovoltaica_autoconsumo"], "soloNuevasDesdeUltimaEjecucion": True}
        Actor.dataset.clear()
        actor_main.descargar = fetch_falso
        actor_main.ESPERA_ENTRE_PAGINAS = 0
        orig_dt = actor_main.datetime

        class FakeDT(orig_dt):
            @classmethod
            def now(cls, tz=None):
                return AHORA

        actor_main.datetime = FakeDT
        try:
            asyncio.run(actor_main.main())
            self.assertEqual([d["expediente"] for d in Actor.dataset], ["EXP-1"])
            self.assertIn("1 licitaciones", Actor.status)
            # Segunda ejecución: nada nuevo
            Actor.dataset.clear()
            asyncio.run(actor_main.main())
            self.assertEqual(Actor.dataset, [])
        finally:
            actor_main.datetime = orig_dt


if __name__ == "__main__":
    unittest.main()
