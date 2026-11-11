"""Comprueba las credenciales SMTP sin enviar nada y explica qué falla, sin mostrar los valores."""
import json
import os
import smtplib
import ssl
import sys
import unicodedata


def revisar(nombre: str) -> bool:
    valor = os.environ.get(nombre, "")
    raros = [(i, c) for i, c in enumerate(valor) if not (c.isascii() and c.isprintable()) or c.isspace()]
    print(f"{nombre}: {len(valor)} caracteres" + (" (vacío)" if not valor else ""))
    for i, c in raros:
        print(f"  posición {i + 1}: carácter no válido {unicodedata.name(c, hex(ord(c)))!r}")
    return bool(valor) and not raros


ok = all([revisar("SMTP_HOST"), revisar("SMTP_PORT"), revisar("SMTP_USER"), revisar("SMTP_PASS")])
usuario = os.environ.get("SMTP_USER", "")
if usuario and not usuario.startswith("AKIA"):
    print("SMTP_USER debería empezar por AKIA (es la 2.ª columna del CSV, no el nombre de usuario de IAM).")
if not ok:
    sys.exit(1)
with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), context=ssl.create_default_context()) as s:
    s.login(usuario, os.environ["SMTP_PASS"])
    print("Conexión e inicio de sesión en SES correctos.")
    # Correo de prueba al primer suscriptor, para comprobar que llega y no cae en spam.
    subs = json.loads(os.environ.get("SUSCRIPTORES") or "[]")
    if subs and os.environ.get("REMITENTE"):
        from email.message import EmailMessage
        m = EmailMessage()
        m["From"], m["To"] = os.environ["REMITENTE"], subs[0]["email"]
        m["Subject"] = "Prueba de envío · Licitaciones Energía"
        m.set_content("Si lees esto en la bandeja de entrada (no en spam), las alertas diarias funcionan.\n"
                      "https://ijfa1982.github.io/licitaciones-energia/")
        s.send_message(m)
        print("Correo de prueba enviado al primer suscriptor.")
