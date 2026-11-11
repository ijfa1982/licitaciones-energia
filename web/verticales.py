"""Webs por sector que comparten el mismo motor (datos, filtros, alertas y cobro).

Cada vertical se publica en una subcarpeta de la web ("" = raíz) y tiene sus sectores, textos, fotos y
enlaces de pago. Para añadir otro sector: una entrada nueva aquí, sus productos en Stripe y sus fotos.
"""
from src.catalogo import GRUPOS, SECTORES, SECTORES_POR_DEFECTO

URL_BASE = "https://ijfa1982.github.io/licitaciones-energia"

VERTICALES = {
    "energia": {
        "ruta": "",
        "sectores": list(SECTORES_POR_DEFECTO),
        "config": {
            "nombre": "Licitaciones Energía",
            "tema": "de energía",
            "stripePro": "https://buy.stripe.com/00w6oH6cQeIifxB4n90VO02",
            "stripeEmpresa": "https://buy.stripe.com/28E4gzcBeas2fxBdXJ0VO03",
        },
        # La web de energía es la plantilla original: no necesita sustituciones.
        "textos": {},
        "fotos": {
            "portada": ("Electric_power_transmission.jpg", "Torres y líneas de alta tensión"),
            "fotovoltaica": ("Solar_Panels.jpg", "Paneles solares fotovoltaicos"),
            "alumbrado": ("LED_streetlight.JPG", "Farola de alumbrado público LED"),
            "electricas": ("Outdoor_power_substation.jpg", "Subestación eléctrica con transformadores"),
            "recarga": ("PV_solar_parking.jpg", "Aparcamiento con marquesina fotovoltaica"),
        },
    },
    "comunicacion": {
        "ruta": "comunicacion",
        "sectores": list(GRUPOS["comunicacion_eventos"]),
        "config": {
            "nombre": "Licitaciones Comunicación y Eventos",
            "tema": "de comunicación y eventos",
            "stripePro": "https://buy.stripe.com/aFa7sLfNqdEeetx8Dp0VO04",
            "stripeEmpresa": "https://buy.stripe.com/8x25kD8kYcAa99daLx0VO05",
        },
        "fotos": {
            "portada": ("Auditorium_of_the_Palacio_de_Congresos_de_Valencia.jpg", "Auditorio de un palacio de congresos"),
            "publicidad": ("Times_Square_1-2.JPG", "Pantallas publicitarias en una plaza"),
            "eventos": ("Conference_room.jpg", "Sala preparada para un congreso"),
            "prensa": ("Press_conference.jpg", "Rueda de prensa"),
            "diseno": ("Video_camera_operator.jpg", "Operador de cámara en una grabación"),
        },
        "textos": {
            "<title>Licitaciones de energía abiertas en España</title>":
                "<title>Licitaciones de comunicación, publicidad y eventos abiertas en España</title>",
            "Licitaciones públicas de fotovoltaica, alumbrado, climatización, puntos de recarga, instalaciones eléctricas y suministro de energía abiertas hoy en España.":
                "Licitaciones públicas de publicidad, marketing, comunicación, relaciones públicas, organización de eventos, ferias y congresos, diseño y producción audiovisual abiertas hoy en España.",
            "Licitaciones de energía abiertas hoy en España":
                "Licitaciones de comunicación y eventos abiertas hoy en España",
            "Fotovoltaica, alumbrado, climatización, puntos de recarga, instalaciones eléctricas y suministro.":
                "Publicidad y marketing, comunicación y relaciones públicas, eventos, ferias y congresos, diseño y producción audiovisual.",
            "<span>Licitaciones Energía</span>": "<span>Licitaciones Comunicación</span>",
            '<summary>¿Qué cuenta como licitación de energía?</summary><p>Fotovoltaica y autoconsumo, eficiencia energética, alumbrado público, climatización y bombas de calor, puntos de recarga, instalaciones eléctricas, suministro de electricidad y gas, almacenamiento, renovables y consultoría energética. Se detectan por los códigos CPV del contrato y por palabras del título, y se descartan las de iluminación de fiestas y eventos.</p>':
                '<summary>¿Qué licitaciones incluye?</summary><p>Campañas de publicidad y marketing, planes de medios, relaciones públicas y gabinetes de prensa, comunicación institucional y redes sociales, organización de eventos, jornadas, ferias y congresos, diseño gráfico e imagen corporativa, y producción de vídeo. Se detectan por los códigos CPV del contrato y por palabras del título.</p>',
            "Sectores (fotovoltaica, alumbrado, climatización, recarga, instalaciones eléctricas, suministro, eficiencia, renovables, consultoría):":
                "Áreas (publicidad y marketing, eventos y ferias, comunicación y relaciones públicas, diseño y audiovisual):",
        },
        "sectores_html": [
            ("publicidad_marketing", "publicidad", "Publicidad y marketing"),
            ("eventos_ferias", "eventos", "Eventos y ferias"),
            ("comunicacion_prensa", "prensa", "Comunicación y prensa"),
            ("diseno_audiovisual", "diseno", "Diseño y audiovisual"),
        ],
    },
}


def url_vertical(clave: str) -> str:
    ruta = VERTICALES[clave]["ruta"]
    return f"{URL_BASE}/{ruta}" if ruta else URL_BASE


def nombres_sectores(clave: str) -> list[str]:
    return [SECTORES[s]["nombre"] for s in VERTICALES[clave]["sectores"]]
