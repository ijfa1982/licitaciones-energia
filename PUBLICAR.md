# Publicar el extractor "Licitaciones de energía en España" en Apify

Tiempo estimado: 20–30 minutos. Usaremos AWS CloudShell, igual que con Mascota Ideal, para no instalar nada en tu ordenador.

## 1. Copia tu token de Apify

1. En Apify Console, abre **Settings → API & Integrations**.
2. Copia tu **Personal API token**. No lo compartas con nadie.

## 2. Sube el código desde CloudShell

1. Abre AWS CloudShell (cualquier región).
2. **Acciones → Cargar archivo** y sube `licitaciones-energia.zip`.
3. Ejecuta, sustituyendo `TU_TOKEN`:

```bash
npm install -g apify-cli
apify login -t TU_TOKEN
unzip -o licitaciones-energia.zip && cd licitaciones-energia
apify push
```

Al terminar verás el enlace al Actor en tu consola. Apify construye la imagen e instala el SDK (unos 2 minutos).

## 3. Primera ejecución de prueba

1. En el Actor, pestaña **Input**: deja los valores por defecto y pulsa **Start**.
2. Cuando termine, revisa la pestaña **Output** (tabla "Resumen") y el **Log**.
3. Envíame el log o una captura de los resultados. El código está probado con un feed de ejemplo construido con la estructura oficial, pero esta es la primera vez que lee el feed real: si algún campo sale vacío, lo ajusto.

## 4. Revisa los sectores con tu criterio

Los códigos CPV y palabras clave de cada sector están en `src/catalogo.py`. Como trabajas en energía, revisa si falta o sobra algo (por ejemplo, CPV de comunidades energéticas o de mantenimiento de subestaciones) y lo añado.

## 5. Publicar en la Store y cobrar

1. En el Actor, pestaña **Publication**: título, descripción, categoría (*Business* / *Lead generation*), icono y el README (se rellena solo desde el código).
2. **Monetization → Pay per event**:
   - Evento principal: resultado del conjunto de datos (`apify-default-dataset-item`), es decir, se cobra por cada licitación devuelta. Precio orientativo: **0,004 $ por licitación** (4 $ por cada 1.000).
   - Evento de inicio (`apify-actor-start`): se activa solo; un precio simbólico como 0,005 $ cubre ejecuciones vacías.
   - Apify te paga el 80 % de lo facturado.
3. Completa tus datos de cobro en la sección de pagos (payouts) de tu cuenta.
4. Publica. Los cambios de precio importantes solo se pueden hacer una vez al mes, así que conviene empezar con un precio prudente.

## 6. Para actualizar

Cuando te envíe una versión nueva: sube el zip a CloudShell y repite `unzip -o licitaciones-energia.zip && cd licitaciones-energia && apify push`.

## Competencia y posicionamiento

Ya existe en la Store al menos un extractor genérico de la Plataforma de Contratación. El nuestro compite por especialización: sectores energéticos listos para usar, detección por palabras del título, filtros de pyme y aviso diario sin duplicados. En la ficha y en las búsquedas hay que insistir en "energía", "fotovoltaica", "alumbrado" y "puntos de recarga".
