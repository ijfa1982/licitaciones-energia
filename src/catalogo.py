"""Catálogos: sectores energéticos (CPV y palabras clave) y tablas de códigos de PLACSP.

Los prefijos CPV se comparan con el inicio del código (sin ceros finales), así que
"0933" cubre 09330000, 09331000, 09331200, etc.
"""

SECTORES = {
    "fotovoltaica_autoconsumo": {
        "nombre": "Fotovoltaica y autoconsumo",
        "cpv": ["0933", "31712331", "45261215"],
        "palabras": [
            "fotovoltaic", "autoconsumo", "placas solares", "paneles solares",
            "planta solar", "instalacion solar", "energia solar", "solar termica",
        ],
    },
    "eficiencia_energetica": {
        "nombre": "Eficiencia energética",
        "cpv": ["713143", "713142"],
        "palabras": [
            "eficiencia energetica", "ahorro energetico", "auditoria energetica",
            "certificacion energetica", "rehabilitacion energetica", "empresa de servicios energeticos",
            "gestion energetica",
        ],
    },
    "alumbrado": {
        "nombre": "Alumbrado público e iluminación",
        # 50232000 general y 502321 alumbrado; fuera 502322 (semáforos y señalización).
        "cpv": ["315", "349285", "453161", "502321", "50232000", "50232110"],
        "palabras": [
            "alumbrado", "luminaria", "tecnologia led", "led", "iluminacion publica",
            "iluminacion exterior", "iluminacion eficiente", "iluminacion vial",
        ],
        # Contratos de suministro eléctrico que citan el alumbrado como punto de consumo: son de suministro.
        "excluir": ["energia electrica", "suministro electrico", "suministro de electricidad"],
    },
    "climatizacion": {
        "nombre": "Climatización, calefacción y bombas de calor",
        "cpv": ["45331", "425", "39715", "5072", "5073", "09323", "42511110"],
        "palabras": [
            "climatizacion", "calefaccion", "aire acondicionado", "aerotermia",
            "geotermia", "bomba de calor", "bombas de calor", "caldera", "red de calor",
        ],
    },
    "suministro_energia": {
        "nombre": "Suministro de electricidad y gas",
        "cpv": ["0931", "653", "09123"],
        "palabras": [
            "suministro electrico", "suministro de electricidad", "suministro de energia electrica",
            "energia electrica", "gas natural",
        ],
    },
    "instalaciones_electricas": {
        "nombre": "Instalaciones eléctricas, media y baja tensión",
        # 45310000 general y 45311/45315/45317 eléctricas; se excluyen 45312 (alarmas y antenas),
        # 45313 (ascensores) y 45314 (telecomunicaciones). De 311 solo generadores (3112) y
        # transformadores (3117): los motores (3111) y el material eléctrico 3168 traían ruido.
        "cpv": ["45310000", "45311", "45315", "45317", "3112", "3117", "50532", "50711"],
        "palabras": [
            "instalacion electrica", "instalaciones electricas", "baja tension", "media tension",
            "alta tension", "centro de transformacion", "grupo electrogeno", "cuadro electrico",
        ],
    },
    "movilidad_electrica": {
        "nombre": "Movilidad eléctrica y puntos de recarga",
        "cpv": ["31158"],
        "palabras": [
            "punto de recarga", "puntos de recarga", "recarga de vehiculos", "recarga electrica",
            "electrolinera", "electrolineras", "cargadores para vehiculos",
        ],
    },
    "almacenamiento_renovables": {
        "nombre": "Almacenamiento y otras renovables",
        "cpv": ["3143", "311213", "45251160"],  # 3144 (pilas y baterías sueltas) no
        "palabras": [
            "almacenamiento energetico", "almacenamiento de energia", "baterias de almacenamiento", "eolic",
            "biomasa", "hidrogeno verde", "comunidad energetica", "comunidades energeticas",
            "minihidraulica",
        ],
    },
    "consultoria_energetica": {
        "nombre": "Ingeniería y consultoría energética",
        "cpv": ["71314", "7132310", "71321"],
        "palabras": ["consultoria energetica", "ingenieria energetica", "plan de transicion energetica"],
    },
    "vehiculos_electricos": {
        "nombre": "Compra de vehículos eléctricos",
        "cpv": ["34144900", "34144910"],
        "palabras": ["vehiculo electrico", "vehiculos electricos", "motorizacion electrica", "autobus electrico"],
    },
}

# Sector fuera de la energía, a petición de clientes de comunicación y eventos. No es de energía, así que
# no se busca por defecto y no le afectan las exclusiones de título (que quitan precisamente los eventos).
SECTORES["comunicacion_eventos"] = {
    "nombre": "Comunicación, publicidad y eventos",
    # 7934 publicidad y marketing, 79413 consultoría de marketing, 79416 relaciones públicas,
    # 7995 organización de eventos, ferias, congresos y seminarios, 79822 diseño gráfico,
    # 92111 producción de películas y vídeos.
    "cpv": ["7934", "79413", "79416", "7995", "79822", "92111"],
    "palabras": [
        "publicidad", "publicitari", "campana de comunicacion", "campanas de comunicacion", "marketing",
        "plan de medios", "comunicacion institucional", "gabinete de prensa", "relaciones publicas",
        "organizacion de eventos", "organizacion de jornadas", "organizacion de congresos", "congreso",
        "feria de", "ferias", "diseno grafico", "merchandising", "produccion audiovisual", "video promocional",
    ],
    "ignora_exclusiones": True,
}

# Sectores que se buscan si el usuario no elige ninguno (la compra de vehículos es opcional:
# interesa a concesionarios, no a instaladores ni empresas de servicios energéticos).
SECTORES_POR_DEFECTO = [k for k in SECTORES if k not in ("vehiculos_electricos", "comunicacion_eventos")]

# Palabras del título que indican que no es un contrato energético aunque coincida algún código
# (iluminación y sonido de eventos, carrozas, fiestas...).
# CPV de material genérico: como CPV secundario solo cuentan si el título también es de energía.
CPV_DEBILES = ["315"]

EXCLUSIONES_TITULO = [
    "sonido", "carroza", "carrozas", "espectaculo", "espectacular", "festejos", "fiestas",
    "iluminacion artistica", "escenario", "escenografia", "evento", "eventos", "musical",
    "navideno", "navidena", "navidad", "alumbrado extraordinario",
    "pantalla", "pantallas", "videowall", "videomarcador", "tira led",
]

# Estado del expediente (ContractFolderStatusCode)
ESTADOS = {
    "PRE": "Anuncio previo",
    "PUB": "En plazo",
    "EV": "Pendiente de adjudicación",
    "ADJ": "Adjudicada",
    "RES": "Resuelta",
    "ANUL": "Anulada",
}

# Tipo de contrato (ProcurementProject/TypeCode)
TIPOS_CONTRATO = {
    "1": "Suministros",
    "2": "Servicios",
    "3": "Obras",
    "21": "Gestión de servicios públicos",
    "22": "Concesión de servicios",
    "31": "Concesión de obras públicas",
    "32": "Concesión de obras",
    "40": "Colaboración público-privada",
    "7": "Administrativo especial",
    "8": "Privado",
    "50": "Patrimonial",
}

# Procedimiento (TenderingProcess/ProcedureCode)
PROCEDIMIENTOS = {
    "1": "Abierto",
    "2": "Restringido",
    "3": "Negociado sin publicidad",
    "4": "Negociado con publicidad",
    "5": "Diálogo competitivo",
    "6": "Contrato menor",
    "7": "Derivado de acuerdo marco",
    "8": "Concurso de proyectos",
    "9": "Abierto simplificado",
    "10": "Asociación para la innovación",
    "100": "Normas internas",
    "999": "Otros",
}

# Comunidades autónomas por código NUTS-2
COMUNIDADES = {
    "ES11": "Galicia",
    "ES12": "Principado de Asturias",
    "ES13": "Cantabria",
    "ES21": "País Vasco",
    "ES22": "Comunidad Foral de Navarra",
    "ES23": "La Rioja",
    "ES24": "Aragón",
    "ES30": "Comunidad de Madrid",
    "ES41": "Castilla y León",
    "ES42": "Castilla-La Mancha",
    "ES43": "Extremadura",
    "ES51": "Cataluña",
    "ES52": "Comunitat Valenciana",
    "ES53": "Illes Balears",
    "ES61": "Andalucía",
    "ES62": "Región de Murcia",
    "ES63": "Ceuta",
    "ES64": "Melilla",
    "ES70": "Canarias",
}

FEED_LICITACIONES = (
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
    "licitacionesPerfilesContratanteCompleto3.atom"
)
FEED_CONTRATOS_MENORES = (
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_1143/"
    "contratosMenoresPerfilesContratantes.atom"
)
HOSTS_OFICIALES = {"contrataciondelsectorpublico.gob.es", "contrataciondelestado.es"}
