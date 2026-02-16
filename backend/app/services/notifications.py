"""IAudit - Email notification service (Resend + SMTP fallback)."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


def _build_alert_html(empresa: dict, consulta: dict) -> str:
    """Build HTML email body for an alert."""
    tipo_labels = {
        "cnd_federal": "CND Federal (Receita Federal / PGFN)",
        "cnd_pr": "CND Paraná (SEFAZ PR)",
        "fgts_regularidade": "FGTS Regularidade (CAIXA)",
    }

    situacao_labels = {
        "negativa": "⚠️ NEGATIVA",
        "irregular": "⚠️ IRREGULAR",
        "erro": "❌ ERRO na Consulta",
    }

    tipo = consulta.get("tipo", "")
    situacao = consulta.get("situacao", "")
    cnpj = empresa.get("cnpj", "")
    razao = empresa.get("razao_social", "")

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #d32f2f; margin-top: 0;">🚨 IAudit — Alerta Fiscal</h2>
            <hr style="border: 1px solid #eee;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #555;">Empresa:</td>
                    <td style="padding: 8px 0;">{razao}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #555;">CNPJ:</td>
                    <td style="padding: 8px 0;">{cnpj}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #555;">Tipo:</td>
                    <td style="padding: 8px 0;">{tipo_labels.get(tipo, tipo)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #555;">Situação:</td>
                    <td style="padding: 8px 0; color: #d32f2f; font-weight: bold;">
                        {situacao_labels.get(situacao, situacao.upper())}
                    </td>
                </tr>
            </table>
            <hr style="border: 1px solid #eee;">
            <p style="color: #888; font-size: 12px;">
                Este alerta foi gerado automaticamente pelo sistema IAudit.<br>
                Acesse o dashboard para mais informações.
            </p>
        </div>
    </body>
    </html>
    """


async def send_alert_email(empresa: dict, consulta: dict) -> bool:
    """
    Send an alert email when CND is negative or FGTS is irregular.

    Tries Resend first, falls back to SMTP.

    Args:
        empresa: Dict with empresa data (must include email_notificacao).
        consulta: Dict with consulta data.

    Returns:
        True if email was sent successfully; False otherwise.
    """
    to_email = empresa.get("email_notificacao")
    if not to_email:
        logger.info(f"No notification email for empresa {empresa.get('cnpj')}. Skipping.")
        return False

    subject = f"🚨 IAudit Alerta: {consulta.get('tipo', '').upper()} — {empresa.get('razao_social', '')}"
    html_body = _build_alert_html(empresa, consulta)

    # Try Resend first
    if settings.resend_api_key:
        try:
            import resend

            resend.api_key = settings.resend_api_key
            resend.Emails.send(
                {
                    "from": settings.email_from,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                }
            )
            logger.info(f"Alert email sent via Resend to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Resend failed: {e}. Trying SMTP fallback.")

    # SMTP fallback
    if settings.smtp_user and settings.smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.email_from
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info(f"Alert email sent via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP failed: {e}")

    logger.warning("No email provider configured. Alert email not sent.")
    return False
