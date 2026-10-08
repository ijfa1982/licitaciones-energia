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


def ejecutar(cfg, ahora=AHORA, **kw):
    guardados = []
    logs = []

    async def guardar(lote):
        guardados.extend(lote)

    actor_main.ESPERA_ENTRE_PAGINAS = 0
    total, vistos = asyncio.run(
        actor_main.recorrer(
            [actor_main.FEED_LICITACIONES], cfg, fetch=fetch_falso, guardar=guardar, log=logs.append,
            max_paginas=kw.get("max_paginas", 10), dias_atras=kw.get("dias_atras", 2),
            max_resultados=kw.get("max_resultados", 1000), ahora=ahora,
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
        # Con 1 día hacia atrás desde la última actualización (8/10 07:00) el límite es el 7/10 07:00;
        # la página 2 aún tiene una entrada de las 09:00 y la 3 es toda antigua: se paran en la 3.
        _, _, _, logs = ejecutar(Config(), dias_atras=1)
        paginas = [l for l in logs if l.startswith("Página")]
        self.assertEqual(len(paginas), 3)

    def test_feed_con_retraso(self):
        # Hoy es 13/10 pero el feed solo llega al 8/10: debe contar los días desde el 8/10.
        ahora = datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc)
        guardados, total, _, logs = ejecutar(Config(), ahora=ahora)
        self.assertEqual([g["expediente"] for g in guardados], ["EXP-1", "EXP-2", "EXP-6", "EXP-7"])
        self.assertTrue(any(l.startswith("Aviso: la última actualización") for l in logs))
        # Los días restantes se siguen calculando desde hoy
        self.assertEqual(guardados[0]["diasRestantes"], 17)

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


class TestCasosReales(unittest.TestCase):
    """Casos sacados de la primera ejecución real (8/10/2026)."""

    CASOS = [
        # (titulo, cpv, debe_entrar)
        ("Suministro de luminarias y equipos de iluminación para la obra del Acondicionamiento Paisajístico", ["31527200"], True),
        ("Suministro e instalación de nuevos equipos de climatización para el CGMACAN", ["42512000"], True),
        ("Instalación de alumbrado público en el camino de los ambeles, Lorca", ["45316110"], True),
        ("Suministro e instalación de alumbrado ornamental en Paseo de Almería", ["31527260"], True),
        ("Suministro de grupo electrógeno.", ["31121000"], True),
        ("Gas Natural para Edificio Sede de la D.P. de la Tgss de Badajoz", ["09000000", "09123000"], True),
        ("Contratación del suministro de gas natural para el Hospital Egarsat", ["09123000"], True),
        ("Suministro de pellet para las calderas de biomasa de la piscina cubierta municipal", ["09111400"], True),
        ("Sustitución de reguladores para el alumbrado aeronáutico de superficie", ["31224600"], True),
        ("Obras de adecuación de edificio para centro social integrado", ["45000000", "45331000"], True),
        # La compra de vehículos eléctricos es un sector opcional, fuera por defecto
        ("Suministro de un vehículo industrial nuevo, motorización eléctrica", ["34100000", "34144900"], False),
        # Falsos positivos de la primera versión
        ("Contrato de servicios de limpieza del Centro Tecnológico", ["90910000", "50730000", "90911000"], False),
        ("Suministro de materiales de ferretería y otros",
         ["44316000", "44110000", "44500000", "39715300", "44800000", "31600000", "31500000"], False),
        ("Suministro de equipamiento técnico especializado para actividades de investigación",
         ["35125300", "44511000", "38300000", "31153000", "31440000", "32342100", "44512000"], False),
        ("Obras de mantenimiento y adecuación interior de la Cafetería",
         ["45453000", "45310000", "45454100", "45451000", "39100000"], False),
        ("Ejecución de obras y mantenimiento del sistema de comunicaciones móviles GSM-R", ["45314000"], False),
        ("Asistencia Técnica en Sonido, Iluminación y Carga/Descarga", ["63100000", "51313000", "71318100"], False),
        ("Suministro en régimen de alquiler de carrozas con servicios de diseño e iluminación", ["79952000", "34220000"], False),
        ("Servicio iluminación artística extraordinaria para los Festejos de San Martin", ["71318100"], False),
        ("Sistemas de iluminación espectacular, sonido y escenario",
         ["32320000", "51310000", "32340000", "31500000", "31527200", "92360000"], False),
        ("Suministro de materiales de obra por lotes",
         ["34991000", "44114000", "44111200", "31500000", "44111100", "14200000", "31000000"], False),
    ]

    def test_casos(self):
        cfg = Config()
        hoy = AHORA.date()
        fallos = []
        for titulo, cpv, esperado in self.CASOS:
            rec = {"estado": "PUB", "titulo": titulo, "cpv": cpv, "fechaLimite": "2026-11-01"}
            obtenido = aceptar(rec, cfg, hoy) is not None
            if obtenido != esperado:
                fallos.append(f"{'debería entrar' if esperado else 'NO debería entrar'}: {titulo}")
        self.assertEqual(fallos, [])

    def test_vehiculos_si_se_eligen(self):
        cfg = Config(sectores=["vehiculos_electricos"])
        rec = {"estado": "PUB", "titulo": "Suministro de un vehículo industrial nuevo, motorización eléctrica",
               "cpv": ["34100000", "34144900"], "fechaLimite": "2026-11-01"}
        salida = aceptar(rec, cfg, AHORA.date())
        self.assertEqual(salida["sectores"], ["Compra de vehículos eléctricos"])

    def test_vehiculos_fuera_por_defecto_desde_input(self):
        self.assertNotIn("vehiculos_electricos", Config.desde_input({}).sectores)
        self.assertNotIn("vehiculos_electricos", Config.desde_input({"sectores": []}).sectores)

    def test_relevancia(self):
        cfg = Config()
        hoy = AHORA.date()
        base = {"estado": "PUB", "fechaLimite": "2026-11-01"}
        alta = aceptar({**base, "titulo": "Suministro de luminarias", "cpv": ["31527200"]}, cfg, hoy)
        media = aceptar({**base, "titulo": "Obras de adecuación de edificio para centro social",
                         "cpv": ["45000000", "45331000"]}, cfg, hoy)
        por_titulo = aceptar({**base, "titulo": "Renovación del alumbrado público", "cpv": ["45000000"]}, cfg, hoy)
        self.assertEqual(alta["relevancia"], "alta")
        self.assertEqual(media["relevancia"], "media")
        self.assertEqual(por_titulo["relevancia"], "alta")


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
