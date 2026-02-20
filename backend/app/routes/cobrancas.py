from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from app.models import BoletoCreate, BoletoResponse, StatusBoleto
from pydantic import BaseModel

from app.services.bradesco import bradesco_service
from app.services.notifications import send_boleto_notification
from app.database import update_boleto_status, create_log
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/registrar", response_model=dict)
async def registrar_boleto(data: BoletoCreate):
    """Registers a new boleto with Bradesco and stores the result."""
    try:
        email = data.pagador_email
        phone = data.pagador_whatsapp or data.pagador_celular

        resp = await bradesco_service.register_boleto(
            data.model_dump(exclude_none=True), recipient_email=email, recipient_phone=phone
        )

        if resp.get("cdErro", 0) != 0:
            raise HTTPException(
                status_code=400,
                detail=resp.get("msgErro", "Erro ao registrar boleto"),
            )

        return {
            "status": "sucesso",
            "nosso_numero": resp.get("nuNossoNumero"),
            "linha_digitavel": resp.get("linhaDigitavel"),
            "bradesco_response": resp,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering boleto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/billing/run-now")
async def run_billing_now(background_tasks: BackgroundTasks):
    """Manually triggers the recurring billing job."""
    from app.services.billing import billing_service

    background_tasks.add_task(billing_service.process_recurring_billing)
    return {"message": "Billing job started in background"}


@router.get("/{nosso_numero}/status")
async def consultar_status(nosso_numero: str):
    """Checks the status of a specific boleto."""
    try:
        status, details = await bradesco_service.consult_status(nosso_numero)
        return {
            "nosso_numero": nosso_numero,
            "status": status,
            "details": details,
        }
    except Exception as e:
        logger.error(f"Error consulting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# WEBHOOK — Bradesco Push Notifications
# ═══════════════════════════════════════════════════════════════════════

@router.post("/webhook")
async def bradesco_webhook(request: Request):
    """
    Process Bradesco webhook events (pagamento, baixa, etc.).

    Bradesco sends status updates here for registered boletos.
    Key status codes:
      - 13: Pago no dia (liquidação no dia)
      - 61: Baixa - Título Pago
      - 06: Liquidado
      - 02: Baixado / Devolvido
    """
    try:
        data = await request.json()
        logger.info(f"Webhook received: {data}")

        nosso_numero = (
            data.get("nuNossoNumero")
            or data.get("nossoNumero")
            or data.get("titulo", {}).get("nuNossoNumero")
        )

        if not nosso_numero:
            logger.warning("Webhook without nosso_numero, ignoring.")
            return {"status": "ignored", "reason": "missing nosso_numero"}

        status_codigo = str(
            data.get("cdSituacaoTitulo")
            or data.get("titulo", {}).get("cdSituacaoTitulo", "")
        )

        # ── Payment Confirmed ────────────────────────────────────────
        if status_codigo in ("13", "61", "06"):
            logger.info(f"Webhook: Payment confirmed for {nosso_numero}")

            try:
                update_boleto_status(nosso_numero, "pago", data)
            except Exception as e:
                logger.error(f"DB update failed for {nosso_numero}: {e}")

            # Extract recipient info from webhook or DB
            pagador_nome = (
                data.get("pagador", {}).get("nome")
                or data.get("titulo", {}).get("nmPagador", "Cliente")
            )
            valor = data.get("vlNominalTitulo") or data.get(
                "titulo", {}).get("vlNominalTitulo", 0
            )
            email = data.get("pagador", {}).get("email")
            phone = data.get("pagador", {}).get("celular")

            await send_boleto_notification(
                "pago",
                {
                    "nomeSacado": pagador_nome,
                    "valorNominal": valor,
                    "dataVencimento": data.get("dtVencimentoTitulo", ""),
                },
                email,
                phone,
            )

            create_log(
                consulta_id="WEBHOOK_PAGO",
                nivel="INFO",
                mensagem=f"Pagamento confirmado via webhook: {nosso_numero}",
                payload=data,
            )

            return {"status": "processed", "event": "payment_confirmed"}

        # ── Baixado / Devolvido ──────────────────────────────────────
        if status_codigo == "02":
            logger.info(f"Webhook: Boleto baixado/devolvido: {nosso_numero}")
            try:
                update_boleto_status(nosso_numero, "baixado", data)
            except Exception as e:
                logger.error(f"DB update failed: {e}")

            create_log(
                consulta_id="WEBHOOK_BAIXA",
                nivel="INFO",
                mensagem=f"Boleto baixado via webhook: {nosso_numero}",
                payload=data,
            )

            return {"status": "processed", "event": "baixa"}

        # ── Unknown status ───────────────────────────────────────────
        logger.info(f"Webhook: unhandled status {status_codigo} for {nosso_numero}")
        return {"status": "received", "unhandled_status": status_codigo}

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error", "detail": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# ESTORNO (Reactivation)
# ═══════════════════════════════════════════════════════════════════════

class EstornoRequest(BaseModel):
    nosso_numero: str
    pagador_nome: str = "Cliente"
    valor: float = 0
    vencimento: str = ""
    linha_digitavel: str = ""
    email: str | None = None
    whatsapp: str | None = None


@router.post("/estorno")
async def estornar_boleto(data: EstornoRequest):
    """Reactivate a cancelled boleto and notify the payer."""
    try:
        boleto_data = {
            "pagador_nome": data.pagador_nome,
            "vlNominal": int(data.valor * 100),
            "dataVencimento": data.vencimento,
            "linhaDigitavel": data.linha_digitavel,
        }

        resp = await bradesco_service.cancel_boleto(
            nosso_numero=data.nosso_numero,
            recipient_email=data.email,
            recipient_phone=data.whatsapp,
            boleto_data=boleto_data,
        )

        if resp.get("cdErro", 0) != 0:
            raise HTTPException(
                status_code=400,
                detail=resp.get("msgErro", "Erro ao estornar boleto"),
            )

        return {"status": "sucesso", "mensagem": "Estorno realizado", "response": resp}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in estorno: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# MANUAL NOTIFICATION & SEARCH (kept from original)
# ═══════════════════════════════════════════════════════════════════════

class NotificationRequest(BaseModel):
    nosso_numero: str
    empresa_nome: str
    valor: float
    vencimento: str
    linha_digitavel: str
    link_boleto: str
    whatsapp: str | None = None
    email: str | None = None
    event_type: str = "emitido"


@router.post("/notify-manual")
async def notify_manual(data: NotificationRequest):
    """Manually triggers a WhatsApp/Email notification for a boleto."""
    try:
        notif_data = {
            "nomeSacado": data.empresa_nome,
            "valorNominal": int(data.valor * 100),
            "dataVencimento": data.vencimento,
            "linhaDigitavel": data.linha_digitavel,
            "linkBoleto": data.link_boleto,
        }

        await send_boleto_notification(
            event=data.event_type,
            data=notif_data,
            recipient_email=data.email,
            recipient_phone=data.whatsapp,
        )

        return {
            "status": "sent",
            "message": f"Notificação ({data.event_type}) enviada para "
            f"{data.whatsapp or data.email}",
        }
    except Exception as e:
        logger.error(f"Error sending manual notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_cobranca(cnpj: str):
    """Search for billing info by CNPJ."""
    from app.database import get_empresa_by_cnpj, get_boletos_by_empresa

    clean_cnpj = "".join(filter(str.isdigit, cnpj))
    empresa = get_empresa_by_cnpj(cnpj)
    if not empresa and len(clean_cnpj) == 14:
        formatted = (
            f"{clean_cnpj[:2]}.{clean_cnpj[2:5]}.{clean_cnpj[5:8]}/"
            f"{clean_cnpj[8:12]}-{clean_cnpj[12:]}"
        )
        empresa = get_empresa_by_cnpj(formatted)

    if not empresa:
        return {"found": False, "message": "Empresa não encontrada"}

    boletos = get_boletos_by_empresa(empresa["id"])

    return {
        "found": True,
        "empresa": {
            "id": empresa["id"],
            "razao_social": empresa["razao_social"],
            "whatsapp": empresa.get("whatsapp"),
            "email": empresa.get("email_notificacao"),
        },
        "boletos": boletos,
    }
