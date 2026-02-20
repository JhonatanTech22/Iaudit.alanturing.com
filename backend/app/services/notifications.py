"""IAudit - Notification Service (SOLID Provider Pattern).

Architecture:
    NotificationProvider (ABC)
    ├── TwilioWhatsAppProvider
    └── SMTPEmailProvider

    NotificationService  ← orchestrates providers + retry queue
"""

from __future__ import annotations

import logging
import smtplib
import uuid
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings
from app.models import CommunicationChannel, CommunicationStatus
from app.services.comunicacao import comm_service
from app.services.settings import dynamic_settings
from app.services.notification_queue import (
    NotificationQueue,
    NotificationTask,
    notification_queue,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# 1. TEMPLATES
# ═══════════════════════════════════════════════════════════════════════

def _format_currency(value: int | float) -> str:
    """Format cents or float to BRL currency string."""
    try:
        val_float = float(value) / 100 if isinstance(value, int) else float(value)
        return f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


# ─── Email HTML Templates ────────────────────────────────────────────

_EMAIL_COLORS = {
    "emitido": "#3b82f6",
    "pago": "#22c55e",
    "atraso": "#ef4444",
    "vencimento_d1": "#f59e0b",
    "reativado": "#8b5cf6",
}

_EMAIL_TITLES = {
    "emitido": "Novo Boleto Disponível",
    "pago": "Pagamento Confirmado",
    "atraso": "Aviso de Atraso",
    "vencimento_d1": "Lembrete de Vencimento",
    "reativado": "Boleto Reativado",
}

_EMAIL_SUBJECTS = {
    "emitido": "Nova Fatura IAudit — Boleto Disponível",
    "pago": "Confirmação de Pagamento — IAudit",
    "atraso": "ALERTA: Fatura em Atraso — IAudit",
    "vencimento_d1": "Lembrete: Vencimento Amanhã — IAudit",
    "reativado": "Fatura Reativada — IAudit",
}


def _build_email_body(event: str, data: dict[str, Any]) -> str:
    """Build the inner HTML body block for each event type."""
    nome = data.get("nomeSacado", "Cliente")
    valor = _format_currency(data.get("valorNominal", 0))
    vencimento = data.get("dataVencimento", "")
    linha = data.get("linhaDigitavel", "")
    qr_pix = data.get("qrCodePix", "")
    link_pdf = data.get("linkPdfBoleto", data.get("linkBoleto", "#"))
    color = _EMAIL_COLORS.get(event, "#3b82f6")

    if event == "emitido":
        pix_block = ""
        if qr_pix:
            pix_block = f"""
            <p style="margin-top: 15px;"><b>Pix Copia e Cola:</b></p>
            <div style="background: #e2e8f0; padding: 10px; font-family: monospace; font-size: 0.8rem; word-break: break-all; border-radius: 4px;">
                {qr_pix}
            </div>
            """
        return f"""
            <p>Olá <b>{nome}</b>,</p>
            <p>Sua fatura IAudit referente aos serviços de monitoramento fiscal está disponível.</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;"><b>Valor:</b> {valor}</p>
                <p style="margin: 5px 0;"><b>Vencimento:</b> {vencimento}</p>
            </div>
            <p>Linha digitável:</p>
            <div style="background: #e2e8f0; padding: 10px; font-family: monospace; text-align: center; border-radius: 4px;">
                {linha}
            </div>
            {pix_block}
            <p style="text-align: center; margin-top: 25px;">
                <a href="{link_pdf}" style="background-color: {color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Baixar Boleto PDF
                </a>
            </p>
        """

    if event == "pago":
        return f"""
            <p>Olá <b>{nome}</b>,</p>
            <p>Confirmamos o recebimento do pagamento do seu boleto.</p>
            <div style="background: #dcfce7; padding: 15px; border-radius: 8px; margin: 20px 0; color: #166534;">
                <p style="margin: 5px 0;"><b>Valor Pago:</b> {valor}</p>
                <p style="margin: 5px 0;"><b>Obrigado por manter sua conta em dia!</b></p>
            </div>
        """

    if event == "atraso":
        return f"""
            <p>Olá <b>{nome}</b>,</p>
            <p>Não identificamos o pagamento do boleto com vencimento em <b>{vencimento}</b>.</p>
            <div style="background: #fee2e2; padding: 15px; border-radius: 8px; margin: 20px 0; color: #991b1b;">
                <p style="margin: 5px 0;"><b>Valor:</b> {valor}</p>
                <p style="margin: 5px 0;">Após o vencimento incidem juros de 0,033%/dia e multa de 2%. Regularize para evitar suspensão dos serviços.</p>
            </div>
            <p style="text-align: center; margin-top: 25px;">
                <a href="{link_pdf}" style="background-color: {color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Visualizar Boleto
                </a>
            </p>
        """

    if event == "vencimento_d1":
        return f"""
            <p>Olá <b>{nome}</b>,</p>
            <p>Lembrete: seu boleto vence <b>amanhã ({vencimento})</b>.</p>
            <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0; color: #92400e;">
                <p style="margin: 5px 0;"><b>Valor:</b> {valor}</p>
                <p style="margin: 5px 0;">Evite juros e multa pagando dentro do prazo.</p>
            </div>
            <p>Linha digitável:</p>
            <div style="background: #e2e8f0; padding: 10px; font-family: monospace; text-align: center; border-radius: 4px;">
                {linha}
            </div>
        """

    if event == "reativado":
        return f"""
            <p>Olá <b>{nome}</b>,</p>
            <p>O boleto abaixo foi <b>reativado</b> e está disponível para pagamento.</p>
            <div style="background: #ede9fe; padding: 15px; border-radius: 8px; margin: 20px 0; color: #5b21b6;">
                <p style="margin: 5px 0;"><b>Valor:</b> {valor}</p>
                <p style="margin: 5px 0;"><b>Vencimento:</b> {vencimento}</p>
            </div>
            <p style="text-align: center; margin-top: 25px;">
                <a href="{link_pdf}" style="background-color: {_EMAIL_COLORS['reativado']}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Visualizar Boleto
                </a>
            </p>
        """

    return f"<p>Notificação sobre seu boleto: {_EMAIL_TITLES.get(event, 'IAudit')}</p>"


def build_boleto_email_html(event: str, data: dict[str, Any]) -> str:
    """Build full HTML email for boleto events."""
    color = _EMAIL_COLORS.get(event, "#3b82f6")
    title = _EMAIL_TITLES.get(event, "Notificação IAudit")
    body_content = _build_email_body(event, data)

    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 40px 0;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background-color: {color}; padding: 20px; text-align: center;">
                <h2 style="color: white; margin: 0; font-size: 24px;">{title}</h2>
            </div>
            <div style="padding: 30px; color: #334155; line-height: 1.6;">
                {body_content}
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                <p style="font-size: 12px; color: #94a3b8; text-align: center;">
                    IAudit — Automação Fiscal Inteligente<br>
                    Este é um email automático, por favor não responda.
                </p>
            </div>
        </div>
    </body>
    </html>
    """


# ─── WhatsApp Text Templates ─────────────────────────────────────────

def build_whatsapp_message(event: str, data: dict[str, Any]) -> str:
    """Build WhatsApp text message with emojis and bold."""
    nome = data.get("nomeSacado", "Cliente")
    valor = _format_currency(data.get("valorNominal", 0))
    vencimento = data.get("dataVencimento", "")
    linha = data.get("linhaDigitavel", "")
    qr_pix = data.get("qrCodePix", "")
    link_pdf = data.get("linkPdfBoleto", data.get("linkBoleto", ""))

    if event == "emitido":
        pix_line = f"\n💳 *Pix Copia e Cola:*\n{qr_pix}" if qr_pix else ""
        return (
            f"📄 *Nova Fatura IAudit*\n\n"
            f"Olá {nome}, seu boleto foi gerado.\n\n"
            f"*Valor:* {valor}\n"
            f"*Vencimento:* {vencimento}\n\n"
            f"📎 *PDF:* {link_pdf}\n\n"
            f"👇 *Linha Digitável:*\n{linha}"
            f"{pix_line}"
        )

    if event == "pago":
        return (
            f"✅ *Pagamento Confirmado — IAudit*\n\n"
            f"Olá {nome}, confirmamos o pagamento de *{valor}*.\n"
            f"Obrigado por manter sua conta em dia!"
        )

    if event == "atraso":
        return (
            f"⚠️ *Aviso de Atraso — IAudit*\n\n"
            f"Olá {nome}, o boleto de *{valor}* venceu em *{vencimento}*.\n"
            f"Após o vencimento incidem juros e multa.\n\n"
            f"📎 *2ª Via:* {link_pdf}"
        )

    if event == "vencimento_d1":
        return (
            f"🔔 *Lembrete de Vencimento — IAudit*\n\n"
            f"Olá {nome}, seu boleto de *{valor}* vence *amanhã ({vencimento})*.\n"
            f"Evite juros pagando dentro do prazo.\n\n"
            f"👇 *Linha Digitável:*\n{linha}"
        )

    if event == "reativado":
        return (
            f"🔄 *Boleto Reativado — IAudit*\n\n"
            f"Olá {nome}, seu boleto de *{valor}* foi reativado e está pronto para pagamento.\n\n"
            f"*Vencimento:* {vencimento}\n"
            f"📎 *PDF:* {link_pdf}"
        )

    return f"IAudit: Notificação sobre boleto {valor}."


# ═══════════════════════════════════════════════════════════════════════
# 2. PROVIDERS (SOLID — Open/Closed Principle)
# ═══════════════════════════════════════════════════════════════════════

class NotificationProvider(ABC):
    """Abstract base for notification channels."""

    @abstractmethod
    async def send(self, recipient: str, subject: str, body: str) -> bool:
        ...

    @property
    @abstractmethod
    def channel_name(self) -> str:
        ...


class SMTPEmailProvider(NotificationProvider):
    """Send email via Resend (primary) or SMTP/Gmail (fallback)."""

    @property
    def channel_name(self) -> str:
        return "email"

    async def send(self, recipient: str, subject: str, body: str) -> bool:
        # 1. Try Resend
        if settings.resend_api_key:
            try:
                import resend
                resend.api_key = settings.resend_api_key
                resend.Emails.send({
                    "from": settings.email_from,
                    "to": [recipient],
                    "subject": subject,
                    "html": body,
                })
                logger.info(f"Email sent via Resend to {recipient}")
                return True
            except Exception as e:
                logger.error(f"Resend failed: {e}. Trying SMTP.")

        # 2. SMTP fallback
        if settings.smtp_user and settings.smtp_password:
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = settings.email_from
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "html"))

                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(msg)

                logger.info(f"Email sent via SMTP to {recipient}")
                return True
            except Exception as e:
                logger.error(f"SMTP failed: {e}")
                return False

        logger.warning("No email provider configured.")
        return False


class TwilioWhatsAppProvider(NotificationProvider):
    """Send WhatsApp message via Twilio."""

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    async def send(self, recipient: str, subject: str, body: str) -> bool:
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            logger.warning("Twilio credentials missing.")
            return False

        try:
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

            # Normalize number → whatsapp:+55XXXXXXXXXXX
            if not recipient.startswith("whatsapp:"):
                clean_num = "".join(filter(str.isdigit, recipient))
                if not clean_num.startswith("55"):
                    clean_num = "55" + clean_num
                recipient = f"whatsapp:+{clean_num}"

            msg = client.messages.create(
                from_=settings.twilio_from_number,
                body=body,   # subject ignored for WhatsApp
                to=recipient,
            )
            logger.info(f"WhatsApp sent to {recipient}. SID: {msg.sid}")
            return True

        except TwilioRestException as e:
            logger.error(f"Twilio API Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Twilio General Error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════
# 3. NOTIFICATION SERVICE (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════

class NotificationService:
    """Unified notification dispatcher with queue-based retry."""

    def __init__(
        self,
        email_provider: NotificationProvider | None = None,
        whatsapp_provider: NotificationProvider | None = None,
        queue: NotificationQueue | None = None,
    ):
        self.email = email_provider or SMTPEmailProvider()
        self.whatsapp = whatsapp_provider or TwilioWhatsAppProvider()
        self.queue = queue or notification_queue

    async def notify(
        self,
        event: str,
        data: dict[str, Any],
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
    ) -> None:
        """Dispatch notification to all applicable channels via the queue."""
        # Check global kill switch
        settings_dict = dynamic_settings.get_settings()
        if not settings_dict.get("mensagens_ativas", True):
            logger.info("Global messaging disabled via dynamic settings.")
            return

        # Email
        if recipient_email:
            subject = _EMAIL_SUBJECTS.get(event, "Notificação IAudit")
            html = build_boleto_email_html(event, data)

            await self.queue.enqueue(NotificationTask(
                task_id=f"{event}-email-{uuid.uuid4().hex[:8]}",
                channel="email",
                send_fn=self._send_email_and_log,
                args=(recipient_email, subject, html, event),
            ))

        # WhatsApp
        if recipient_phone and settings.twilio_account_sid:
            text_msg = build_whatsapp_message(event, data)

            await self.queue.enqueue(NotificationTask(
                task_id=f"{event}-whatsapp-{uuid.uuid4().hex[:8]}",
                channel="whatsapp",
                send_fn=self._send_whatsapp_and_log,
                args=(recipient_phone, text_msg, event),
            ))

    # ── Internal: send + log ─────────────────────────────────────────

    async def _send_email_and_log(
        self, recipient: str, subject: str, html: str, event: str
    ) -> bool:
        success = await self.email.send(recipient, subject, html)
        await comm_service.log_message(
            channel=CommunicationChannel.email,
            recipient=recipient,
            subject=subject,
            content=f"Template: {event}",
            status=CommunicationStatus.sent if success else CommunicationStatus.failed,
        )
        return success

    async def _send_whatsapp_and_log(
        self, recipient: str, text_msg: str, event: str
    ) -> bool:
        success = await self.whatsapp.send(recipient, "", text_msg)
        await comm_service.log_message(
            channel=CommunicationChannel.whatsapp,
            recipient=recipient,
            content=text_msg,
            status=CommunicationStatus.sent if success else CommunicationStatus.failed,
        )
        return success


# ─── Singleton & Backwards-Compatible API ────────────────────────────

notification_service = NotificationService()


async def send_boleto_notification(
    event: str,
    data: dict[str, Any],
    recipient_email: str | None = None,
    recipient_phone: str | None = None,
) -> None:
    """Drop-in replacement for legacy function signature."""
    await notification_service.notify(event, data, recipient_email, recipient_phone)


# ── Legacy Alert (kept for scheduler.py compatibility) ───────────────

async def send_alert_email(empresa: dict, consulta: dict) -> bool:
    """Alert when CND is negative or FGTS is irregular."""
    to_email = empresa.get("email_notificacao")
    if not to_email:
        return False

    tipo = consulta.get("tipo", "")
    situacao = consulta.get("situacao", "").upper()

    subject = f"🚨 Alerta: {tipo.upper()} — {empresa.get('razao_social')}"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>🚨 Alerta Fiscal: {tipo}</h2>
        <p>Empresa: {empresa.get('razao_social')}</p>
        <p>CNPJ: {empresa.get('cnpj')}</p>
        <p>Situação: <b style="color:red">{situacao}</b></p>
        <hr>
        <p style="font-size: 12px; color: #94a3b8;">IAudit — Automação Fiscal</p>
    </body>
    </html>
    """

    provider = SMTPEmailProvider()
    success = await provider.send(to_email, subject, html)

    await comm_service.log_message(
        channel=CommunicationChannel.email,
        recipient=to_email,
        subject=subject,
        content="Alert Email",
        status=CommunicationStatus.sent if success else CommunicationStatus.failed,
    )
    return success
