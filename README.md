# Licitaciones de energía en España (PLACSP)

Encuentra cada día las **licitaciones públicas del sector energético** publicadas en la Plataforma de Contratación del Sector Público: fotovoltaica y autoconsumo, eficiencia energética, alumbrado público, climatización y bombas de calor, puntos de recarga, instalaciones eléctricas, suministro de electricidad y gas, almacenamiento y renovables.

Pensado para **instaladores, ingenierías, ESE y comercializadoras** que no tienen tiempo de revisar miles de anuncios: devuelve solo lo que les interesa, con presupuesto, plazo, órgano de contratación y enlace a la ficha oficial y a los pliegos.

*English: Spanish public tenders for the energy sector (solar PV, energy efficiency, street lighting, HVAC, EV charging, electrical installations, power supply), filtered by sector, region, budget and deadline, from Spain's official procurement platform.*

## Qué lo diferencia

- **Filtro energético listo para usar**: 9 sectores definidos por códigos CPV y por palabras del título, para captar también licitaciones mal clasificadas (por ejemplo, una renovación de alumbrado LED registrada como "obras").
- **Menos ruido**: un código CPV energético solo cuenta si es el principal del contrato o si al menos la mitad de sus códigos son energéticos, y se excluyen la iluminación y el sonido de eventos y fiestas. Cada resultado indica su relevancia (alta o media).
- **Solo lo que está en plazo**: por defecto, licitaciones abiertas con fecha límite futura y días restantes calculados.
- **Aviso diario sin duplicados**: con *"Solo nuevas o modificadas desde la última ejecución"* y una tarea programada, recibes únicamente lo nuevo.
- **Filtros de pyme**: comunidad autónoma, presupuesto mínimo y máximo, contratos menores opcionales.
- **Datos oficiales**: usa la sindicación ATOM de datos abiertos del Ministerio de Hacienda, sin entrar en páginas web.

## Cómo usarlo

1. Elige los sectores y, si quieres, las comunidades autónomas.
2. Ajusta presupuesto y días hacia atrás (2 para un aviso diario).
3. Ejecuta. Descarga el resultado en Excel, CSV o JSON, o conéctalo a tu correo, Google Sheets o Slack con las integraciones de Apify.

Para un aviso diario: crea una **Tarea** con tu configuración, activa *"Solo nuevas o modificadas"* y prográmala cada mañana.

## Ejemplo de entrada

```json
{
  "sectores": ["fotovoltaica_autoconsumo", "alumbrado"],
  "comunidades": ["ES51", "ES52"],
  "presupuestoMaximo": 500000,
  "diasAtras": 2,
  "soloNuevasDesdeUltimaEjecucion": true
}
```

## Ejemplo de resultado

```json
{
  "expediente": "2026/1234",
  "titulo": "Suministro e instalación de planta fotovoltaica para autoconsumo en el polideportivo",
  "sectores": ["Fotovoltaica y autoconsumo"],
  "motivoCoincidencia": ["CPV 09331200"],
  "estadoTexto": "En plazo",
  "organoContratacion": "Ayuntamiento de Ejemplo",
  "organoNif": "P0800000X",
  "tipoContrato": "Suministros",
  "procedimiento": "Abierto",
  "presupuestoSinIva": 150000,
  "presupuestoConIva": 181500,
  "comunidadAutonoma": "Cataluña",
  "lugarEjecucion": "Barcelona",
  "fechaLimite": "2026-10-30",
  "horaLimite": "14:00",
  "diasRestantes": 22,
  "cpv": ["09331200", "45261215"],
  "documentos": [{ "tipo": "Pliego administrativo", "nombre": "PCAP.pdf", "url": "https://..." }],
  "urlDetalle": "https://contrataciondelsectorpublico.gob.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=..."
}
```

## Campos principales

| Campo | Qué es |
| --- | --- |
| `titulo`, `expediente` | Objeto del contrato y número de expediente |
| `sectores`, `motivoCoincidencia` | Sector energético detectado y por qué (CPV o palabra del título) |
| `relevancia` | `alta`: la energía es el objeto principal del contrato. `media`: es una parte importante de un contrato más amplio (por ejemplo, una obra de edificio con climatización) |
| `estado`, `estadoTexto` | PUB = en plazo, EV = pendiente de adjudicación, ADJ = adjudicada… |
| `organoContratacion`, `organoNif`, `organosSuperiores` | Quién contrata |
| `presupuestoSinIva`, `presupuestoConIva`, `valorEstimado` | Importes en euros |
| `comunidadAutonoma`, `codigoNuts`, `lugarEjecucion`, `municipio` | Dónde se ejecuta |
| `fechaLimite`, `horaLimite`, `diasRestantes` | Plazo de presentación de ofertas |
| `documentos` | Enlaces a pliegos y documentos |
| `adjudicatario`, `importeAdjudicacion` | Cuando ya está adjudicada |
| `urlDetalle` | Ficha oficial en la Plataforma |

## Fuente y limitaciones

- Fuente: [conjunto de datos abiertos de licitaciones](https://www.hacienda.gob.es/es-ES/GobiernoAbierto/Datos%20Abiertos/Paginas/LicitacionesContratante.aspx) de la Plataforma de Contratación del Sector Público (Ministerio de Hacienda), publicado para su reutilización.
- Cubre los órganos que publican en la Plataforma estatal. Algunas comunidades (por ejemplo, Cataluña, País Vasco o Andalucía) tienen además sus propias plataformas; sus licitaciones solo aparecen si también se agregan a la estatal.
- La clasificación por sector usa CPV y palabras clave: revisa siempre el pliego antes de presentar una oferta.

## Precio

Pagas por cada licitación devuelta, no por el tiempo de ejecución. Un aviso diario para un sector y una comunidad suele devolver pocas licitaciones al día.
