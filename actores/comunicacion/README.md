# Licitaciones de comunicación, publicidad y eventos en España

Encuentra cada día las **licitaciones públicas de comunicación, publicidad y eventos** publicadas en la Plataforma de Contratación del Sector Público: campañas de publicidad y marketing, planes de medios, organización de eventos, jornadas, ferias y congresos, gabinetes de prensa, relaciones públicas y redes sociales, diseño gráfico e imagen corporativa, y producción de vídeo.

Pensado para **agencias de publicidad y comunicación, productoras, organizadores de eventos, estudios de diseño y consultoras de desarrollo de negocio** que no tienen tiempo de revisar miles de anuncios: devuelve solo lo que les interesa, con presupuesto, plazo, órgano de contratación y enlace a la ficha oficial y a los pliegos.

*English: Spanish public tenders for advertising, marketing, PR, events, trade fairs and congresses, graphic design and video production, filtered by area, region, budget and deadline, from Spain's official procurement platform.*

## Qué lo diferencia

- **Cuatro áreas listas para usar**: publicidad y marketing; eventos, ferias y congresos; comunicación y relaciones públicas; diseño y producción audiovisual. Se detectan por códigos CPV y por palabras del título, para captar también licitaciones mal clasificadas.
- **Solo lo que está en plazo**: por defecto, licitaciones abiertas con fecha límite futura y días restantes calculados.
- **Aviso diario sin duplicados**: con *"Solo nuevas o modificadas desde la última ejecución"* y una tarea programada, recibes únicamente lo nuevo.
- **Filtros de pyme**: comunidad autónoma, presupuesto mínimo y máximo, contratos menores opcionales, palabras clave propias.
- **Datos oficiales**: sindicación ATOM de datos abiertos del Ministerio de Hacienda.

## Cómo usarlo

1. Elige las áreas (o ninguna, para todas) y, si quieres, las comunidades autónomas.
2. Ajusta presupuesto y días hacia atrás (2 para un aviso diario).
3. Ejecuta. Descarga el resultado en Excel, CSV o JSON, o conéctalo a tu correo, Google Sheets o Slack con las integraciones de Apify.

## Ejemplo de entrada

```json
{
  "sectores": ["eventos_ferias", "publicidad_marketing"],
  "comunidades": ["ES30", "ES61"],
  "presupuestoMinimo": 15000,
  "diasAtras": 2
}
```

## Campos principales

| Campo | Qué es |
|---|---|
| `titulo`, `organoContratacion` | Objeto del contrato y quién licita |
| `sectores`, `motivoCoincidencia` | Área detectada y por qué (CPV o palabra del título) |
| `presupuestoSinIva`, `valorEstimado` | Importes en euros |
| `fechaLimite`, `diasRestantes` | Plazo de presentación de ofertas |
| `comunidadAutonoma`, `municipio` | Lugar de ejecución |
| `urlDetalle`, `documentos` | Ficha oficial y pliegos |
| `adjudicatarios` | Empresas ganadoras, NIF e importe (en licitaciones adjudicadas) |

## Fuente y limitaciones

Datos de la Plataforma de Contratación del Sector Público, reutilizados conforme a la Ley 37/2007. Incluye la Administración General del Estado, muchas comunidades autónomas y miles de ayuntamientos; algunas comunidades publican parte de sus contratos solo en su plataforma propia. La información es orientativa: consulta siempre los pliegos oficiales antes de presentar una oferta. Este Actor no está vinculado a ninguna Administración.

También disponible: **Licitaciones de energía en España** (fotovoltaica, alumbrado, climatización, recarga, instalaciones eléctricas y suministro), del mismo autor.
