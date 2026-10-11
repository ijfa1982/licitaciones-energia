# Web y app de licitaciones: puesta en marcha y cobro

La web vive en `web/site` y se publica gratis en GitHub Pages:
https://ijfa1982.github.io/licitaciones-energia

Cada mañana, GitHub Actions (`.github/workflows/web.yml`) lee el feed oficial de la Plataforma de
Contratación con el mismo código del Actor, actualiza la web y envía las alertas a los suscriptores.
No gasta saldo de Apify.

## 1. Publicar la web (una vez)
1. GitHub → repositorio `licitaciones-energia` → Settings → Pages → Source: **GitHub Actions**.
   (Pages gratis exige que el repositorio sea público.)
2. Pestaña Actions → "Web y alertas" → **Run workflow**. La primera vez tarda unos 20 minutos.

## 2. Cobrar con Stripe
1. Crear cuenta en stripe.com (gratis; comisión ~1,5 % + 0,25 € por cobro con tarjeta europea).
2. Activar Stripe Tax o configurar IVA 21 % (precios "sin IVA incluido").
3. Productos → crear "Plan Pro" 19 €/mes y "Plan Empresa" 49 €/mes (recurrente mensual).
4. Payment Links → un enlace por plan:
   - Recoger nombre de empresa y NIF (campo personalizado) y dirección de facturación.
   - Tras el pago, redirigir a `https://ijfa1982.github.io/licitaciones-energia/gracias.html`.
   - Opcional: 7 días de prueba gratis.
5. Configuración → Portal de clientes → activar (bajas y cambio de tarjeta) y copiar su enlace.
6. Pasar a Claude los dos enlaces de pago, el del portal y los datos del aviso legal; se ponen en `web/site/config.js`.

## 3. Alertas por email
Secretos del repositorio (Settings → Secrets and variables → Actions):
- `SMTP_HOST` = smtp.gmail.com · `SMTP_PORT` = 465
- `SMTP_USER` = cuenta de Gmail que envía · `SMTP_PASS` = contraseña de aplicación de Google
- `REMITENTE` = "Licitaciones Energía <cuenta@gmail.com>"
- `SUSCRIPTORES` = lista JSON de clientes (formato en `web/enviar_alertas.py`).
Cada alta nueva: añadir al cliente en `SUSCRIPTORES` con los filtros que envió desde `gracias.html`.

## 4. Antes de cobrar
- Alta como autónomo (IAE 763/769 o similar de servicios informáticos) y facturas con IVA.
- Completar titular, NIF, domicilio y email en `config.js` (aviso legal obligatorio por la LSSI).

## App móvil
La web es instalable como app (PWA): Android "Instalar aplicación", iPhone "Añadir a pantalla de inicio".
Para Google Play se puede empaquetar la misma web con Bubblewrap/TWA (cuenta de desarrollador: 25 $ una vez).
