"""
Servicio de envío de correos electrónicos (SMTP / Consola de desarrollo).

Soporte dual:
- Si SMTP_HOST y SMTP_USUARIO están configurados en .env, realiza el envío real
  por SMTP (con STARTTLS o SSL).
- Si no están configurados, registra el correo en la consola/terminal del backend
  para facilitar pruebas locales sin requerir credenciales externas.
"""
import asyncio
import json
import logging
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.nucleo.config import obtener_config
from app.nucleo.errores import ErrorNegocio

logger = logging.getLogger("app.correo")


def _construir_mensaje_html(nombre: str, enlace: str, minutos: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Recuperación de contraseña</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;">
    <tr>
      <td style="background-color: #12306B; padding: 28px 32px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">
          Unidad Educativa "Mariscal Sucre G"
        </h1>
        <p style="color: #cbd5e1; margin: 6px 0 0 0; font-size: 13px;">Sistema de Información y Gestión Escolar</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px;">
        <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">Estimado(a) {nombre}:</h2>
        <p style="font-size: 15px; line-height: 1.6; color: #334155;">
          Hemos recibido una solicitud para restablecer la contraseña de acceso a su cuenta en el sistema escolar.
        </p>
        <p style="font-size: 15px; line-height: 1.6; color: #334155;">
          Para establecer una nueva contraseña segura, haga clic en el siguiente botón:
        </p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{enlace}" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 15px; font-weight: 600; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);">
            Establecer nueva contraseña
          </a>
        </div>
        <div style="background-color: #f1f5f9; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 4px; margin: 24px 0;">
          <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.5;">
            <strong>Nota de seguridad:</strong> Este enlace es de <strong>un solo uso</strong> y caducará en <strong>{minutos} minutos</strong>.
            Si usted no solicitó este cambio, puede ignorar este mensaje; su cuenta continuará protegida con su contraseña actual.
          </p>
        </div>
        <p style="font-size: 13px; color: #64748b; margin-top: 24px; word-break: break-all;">
          Si tiene problemas con el botón, copie y pegue este enlace en su navegador:<br>
          <a href="{enlace}" style="color: #2563eb;">{enlace}</a>
        </p>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 16px 32px; text-align: center; border-top: 1px solid #e2e8f0;">
        <p style="margin: 0; font-size: 12px; color: #94a3b8;">
          Este es un correo automático generado por el Sistema Escolar. Por favor, no responda a este mensaje.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _enviar_smtp_sincrono(destinatario: str, asunto: str, cuerpo_html: str, cuerpo_texto: str) -> None:
    cfg = obtener_config()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = cfg.SMTP_REMITENTE
    msg["To"] = destinatario

    msg.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    try:
        server = smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=15)
        if cfg.SMTP_USAR_TLS:
            server.starttls()
        if cfg.SMTP_USUARIO and cfg.SMTP_PASSWORD:
            server.login(cfg.SMTP_USUARIO, cfg.SMTP_PASSWORD)
        server.sendmail(cfg.SMTP_REMITENTE, [destinatario], msg.as_string())
        server.quit()
        logger.info("Correo enviado exitosamente por SMTP a %s", destinatario)
    except Exception as exc:
        logger.error("Fallo al enviar correo por SMTP a %s: %s", destinatario, exc)
        raise ErrorNegocio("No se pudo enviar el correo de recuperación. Intente más tarde.", "error_correo") from exc


def _enviar_brevo_sincrono(destinatario: str, nombre: str, asunto: str, cuerpo_html: str, cuerpo_texto: str) -> None:
    """Envía el correo por la API HTTPS de Brevo (funciona en Railway sin plan Pro)."""
    cfg = obtener_config()
    datos = {
        "sender": {"name": "U.E. Mariscal Sucre G", "email": cfg.SMTP_REMITENTE},
        "to": [{"email": destinatario, "name": nombre}],
        "subject": asunto,
        "htmlContent": cuerpo_html,
        "textContent": cuerpo_texto,
    }
    peticion = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(datos).encode("utf-8"),
        headers={"api-key": cfg.BREVO_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=15):
            pass
        logger.info("Correo enviado por Brevo a %s", destinatario)
    except Exception as exc:
        logger.error("Fallo al enviar correo por Brevo a %s: %s", destinatario, exc)
        raise ErrorNegocio("No se pudo enviar el correo de recuperación. Intente más tarde.", "error_correo") from exc


async def enviar_correo_recuperacion(destinatario: str, nombre: str, enlace: str, minutos: int = 15) -> None:
    """Envía el correo de recuperación al destinatario usando Brevo, SMTP o consola en local."""
    cfg = obtener_config()
    asunto = "Recuperación de contraseña — Unidad Educativa Mariscal Sucre G"
    cuerpo_texto = (
        f"Estimado(a) {nombre}:\n\n"
        f"Para restablecer su contraseña de acceso al Sistema Escolar, visite el siguiente enlace:\n"
        f"{enlace}\n\n"
        f"Este enlace es de un solo uso y caduca en {minutos} minutos.\n"
        f"Si no solicitó este cambio, ignore este mensaje."
    )
    cuerpo_html = _construir_mensaje_html(nombre, enlace, minutos)

    if cfg.BREVO_API_KEY:
        # Envío por API HTTPS (producción en Railway)
        await asyncio.to_thread(_enviar_brevo_sincrono, destinatario, nombre, asunto, cuerpo_html, cuerpo_texto)
    elif cfg.SMTP_HOST and cfg.SMTP_USUARIO:
        # Envío real a través del servidor SMTP configurado
        await asyncio.to_thread(_enviar_smtp_sincrono, destinatario, asunto, cuerpo_html, cuerpo_texto)
    else:
        # Modo desarrollo / emulado en consola
        if cfg.CORREO_EN_CONSOLA:
            print("\n" + "=" * 80)
            print("[CORREO DE RECUPERACIÓN - SIMULADOR EN CONSOLA]")
            print(f"Para: {destinatario} ({nombre})")
            print(f"Asunto: {asunto}")
            print(f"Caducidad: {minutos} minutos (un solo uso)")
            print(f"Enlace seguro:")
            print(f"-> {enlace}")
            print("=" * 80 + "\n")
        logger.info("Correo simulado para %s", destinatario)
