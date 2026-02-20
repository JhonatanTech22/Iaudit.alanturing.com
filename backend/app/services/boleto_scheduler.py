"""IAudit - Boleto Vencimento Scheduler (D-1 / D+1).

Daily cron job that scans active boletos and dispatches:
  - D-1: "Lembrete de Vencimento" for boletos due tomorrow
  - D+1: "Aviso de Atraso"       for boletos overdue (past vencimento)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta, date

from app.config import settings
from app.database import (
    get_boletos_ativos,
    create_log,
)
from app.services.notifications import send_boleto_notification

logger = logging.getLogger(__name__)


def _parse_date(value) -> date | None:
    """Parse a date from string or date object."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


async def check_boleto_vencimentos():
    """
    Daily cron (07:00) — scans all active boletos for D-1 and D+1 alerts.

    D-1: status='emitido', data_vencimento = tomorrow
         → "Lembrete de Vencimento"

    D+1: status='emitido' or 'atraso', data_vencimento < today
         → "Aviso de Atraso" (only first time or weekly reminder)
    """
    logger.info("=== Job: Check Boleto Vencimentos (D-1 / D+1) ===")

    try:
        boletos = get_boletos_ativos()
    except Exception as e:
        logger.error(f"Failed to fetch active boletos: {e}")
        return

    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)

    d1_count = 0
    d_plus_count = 0

    for boleto in boletos:
        boleto_id = boleto.get("id", "?")
        status = boleto.get("status", "")
        vencimento_raw = boleto.get("data_vencimento") or boleto.get("dataVencimento")
        venc_date = _parse_date(vencimento_raw)

        if not venc_date:
            continue

        # Build notification payload
        notif_data = {
            "nomeSacado": boleto.get("pagador_nome", "Cliente"),
            "valorNominal": boleto.get("vl_nominal") or boleto.get("valor", 0),
            "dataVencimento": venc_date.strftime("%d/%m/%Y"),
            "linhaDigitavel": boleto.get("linha_digitavel", ""),
            "linkPdfBoleto": (
                f"{settings.backend_url}/api/boleto/pdf/"
                f"{boleto.get('nosso_numero', boleto_id)}"
            ),
        }

        email = boleto.get("email_notificacao") or boleto.get("pagador_email")
        phone = boleto.get("whatsapp") or boleto.get("pagador_whatsapp")

        # ── D-1: Vence amanhã ────────────────────────────────────────
        if venc_date == tomorrow and status in ("emitido", "01"):
            logger.info(f"D-1 alert for boleto {boleto_id} (venc: {venc_date})")

            try:
                await send_boleto_notification(
                    "vencimento_d1", notif_data, email, phone
                )
                d1_count += 1
                create_log(
                    consulta_id="BOLETO_D1",
                    nivel="INFO",
                    mensagem=f"Lembrete D-1 enviado: {boleto_id}",
                )
            except Exception as e:
                logger.error(f"D-1 notification failed for {boleto_id}: {e}")

        # ── D+1: Vencido ─────────────────────────────────────────────
        elif venc_date < today and status in ("emitido", "01", "atraso"):
            dias_atraso = (today - venc_date).days

            # Notify on D+1, D+3, D+7, then weekly
            should_notify = dias_atraso in (1, 3, 7) or (dias_atraso > 7 and dias_atraso % 7 == 0)

            if should_notify:
                logger.info(
                    f"D+{dias_atraso} alert for boleto {boleto_id} (venc: {venc_date})"
                )
                notif_data["diasAtraso"] = dias_atraso

                try:
                    await send_boleto_notification(
                        "atraso", notif_data, email, phone
                    )
                    d_plus_count += 1
                    create_log(
                        consulta_id="BOLETO_ATRASO",
                        nivel="WARN",
                        mensagem=f"Alerta D+{dias_atraso} enviado: {boleto_id}",
                    )
                except Exception as e:
                    logger.error(f"D+ notification failed for {boleto_id}: {e}")

    logger.info(
        f"Vencimento check complete. D-1 sent: {d1_count}, D+ sent: {d_plus_count}"
    )
