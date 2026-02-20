"""
IAudit - BoletoService
Core business logic for billing management.
Ported from TypeScript modulo-cobranca/BoletoService.ts
"""

import re
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Any

from app.services.bradesco import bradesco_service
from app.services.notifications import send_boleto_notification
from app.database import create_log

logger = logging.getLogger(__name__)

# Bradesco status codes (from API v1.7.1)
STATUS_A_VENCER = "01"
STATUS_PAGO = "61"
STATUS_PROTESTO = "04"
STATUS_BAIXADO = "57"
STATUS_CANCELADO = "05"
STATUS_PAGO_PARCIAL = "62"
STATUS_PENDENTE = "00"

MOTIVOS_BAIXA = {
    "1": "Pago em dinheiro",
    "2": "Pago em cheque",
    "3": "Protesto",
    "4": "Devolução",
    "5": "Desconto",
    "6": "Acerto",
    "7": "Outros",
}


class BoletoService:
    """Orchestrates boleto operations: emission, query, cancelation, protest."""

    # ========================= EMISSION =========================

    async def emitir_boleto(self, dados: dict, usuario_id: str = "system") -> dict:
        """
        Emit a single boleto.
        1. Validate data
        2. Call Bradesco API
        3. Log history
        4. Trigger notifications
        """
        try:
            # 1. Validate payer data
            pagador_doc = dados.get("pagador_documento", "")
            if pagador_doc and not self.validar_cpf_cnpj(pagador_doc):
                return {"sucesso": False, "erro": "CPF/CNPJ do pagador inválido"}

            pagador_nome = dados.get("pagador_nome", "")
            if not pagador_nome:
                return {"sucesso": False, "erro": "Nome do pagador é obrigatório"}

            vl_nominal = dados.get("vlNominal", 0)
            if vl_nominal <= 0:
                return {"sucesso": False, "erro": "Valor deve ser maior que zero"}

            # 2. Call Bradesco
            email = dados.get("pagador_email")
            phone = dados.get("pagador_whatsapp") or dados.get("pagador_celular")

            resp = await bradesco_service.register_boleto(
                dados,
                recipient_email=email,
                recipient_phone=phone
            )

            # 3. Check response
            if resp.get("cdErro", 0) != 0:
                return {
                    "sucesso": False,
                    "erro": resp.get("msgErro", "Erro ao registrar boleto"),
                    "codigoErro": resp.get("cdErro"),
                }

            # 4. Extract key data
            nosso_numero = resp.get("nuNossoNumero")
            linha_digitavel = resp.get("linhaDigitavel", "")
            if not linha_digitavel and "listaRegistro" in resp:
                linha_digitavel = resp["listaRegistro"][0].get("linhaDigitavel", "")

            # 5. Log history
            create_log(
                consulta_id="BOLETO_EMISSAO",
                nivel="INFO",
                mensagem=f"Boleto emitido: {nosso_numero} por {usuario_id}",
                payload={
                    "nosso_numero": nosso_numero,
                    "valor": vl_nominal,
                    "vencimento": str(dados.get("dataVencimento")),
                    "pagador": pagador_nome,
                    "tipo_alteracao": "REGISTRO",
                    "status_novo": STATUS_PENDENTE,
                    "origem": "API",
                }
            )

            return {
                "sucesso": True,
                "nosso_numero": nosso_numero,
                "linha_digitavel": linha_digitavel,
                "bradesco_response": resp,
            }

        except Exception as e:
            logger.error(f"[BoletoService] Erro ao emitir: {e}")
            return {"sucesso": False, "erro": str(e)}

    async def emitir_lote(self, boletos: list[dict], usuario_id: str = "system") -> dict:
        """Emit multiple boletos in batch (max 100)."""
        if not boletos:
            return {"sucesso": False, "erro": "Lista de boletos vazia"}
        if len(boletos) > 100:
            return {"sucesso": False, "erro": "Limite máximo de 100 boletos por lote"}

        resultados = []
        for boleto in boletos:
            resultado = await self.emitir_boleto(boleto, usuario_id)
            resultados.append(resultado)

        sucessos = sum(1 for r in resultados if r.get("sucesso"))
        erros = sum(1 for r in resultados if not r.get("sucesso"))

        return {
            "sucesso": True,
            "resumo": {"total": len(boletos), "sucessos": sucessos, "erros": erros},
            "resultados": resultados,
        }

    # ========================= QUERY & UPDATE =========================

    async def consultar_e_atualizar(self, nosso_numero: str) -> dict:
        """Query Bradesco for current status and update locally."""
        try:
            status, details = await bradesco_service.consult_status(nosso_numero)

            create_log(
                consulta_id="BOLETO_CONSULTA",
                nivel="INFO",
                mensagem=f"Status consultado: {nosso_numero} → {status}",
                payload={
                    "nosso_numero": nosso_numero,
                    "status": status,
                    "tipo_alteracao": "CONSULTA",
                    "origem": "API",
                }
            )

            return {
                "sucesso": True,
                "nosso_numero": nosso_numero,
                "status": status,
                "detalhes": details,
            }
        except Exception as e:
            logger.error(f"[BoletoService] Erro ao consultar: {e}")
            return {"sucesso": False, "erro": str(e)}

    # ========================= BAIXA (CANCELATION) =========================

    async def baixar_boleto(self, nosso_numero: str, motivo: str, usuario_id: str = "system") -> dict:
        """Request boleto cancellation/write-off."""
        if motivo not in MOTIVOS_BAIXA:
            return {
                "sucesso": False,
                "erro": "Motivo de baixa inválido",
                "motivos_permitidos": MOTIVOS_BAIXA,
            }

        try:
            resp = await bradesco_service.baixar_boleto_api(nosso_numero, motivo)

            if resp.get("cdErro", 0) != 0:
                return {"sucesso": False, "erro": resp.get("msgErro", "Erro ao baixar boleto")}

            create_log(
                consulta_id="BOLETO_BAIXA",
                nivel="INFO",
                mensagem=f"Boleto baixado: {nosso_numero} (motivo: {MOTIVOS_BAIXA[motivo]}) por {usuario_id}",
                payload={
                    "nosso_numero": nosso_numero,
                    "motivo": motivo,
                    "descricao_motivo": MOTIVOS_BAIXA[motivo],
                    "tipo_alteracao": "BAIXA",
                    "status_novo": STATUS_BAIXADO,
                    "origem": "MANUAL",
                    "alterado_por": usuario_id,
                }
            )

            return {"sucesso": True, "mensagem": "Baixa solicitada com sucesso"}

        except Exception as e:
            logger.error(f"[BoletoService] Erro ao baixar: {e}")
            return {"sucesso": False, "erro": str(e)}

    # ========================= PROTEST =========================

    async def protestar_boleto(
        self, nosso_numero: str, tipo: str = "protesto", usuario_id: str = "system"
    ) -> dict:
        """Request protest or credit bureau listing."""
        try:
            codigo_funcao = "3" if tipo == "negativacao" else "1"

            resp = await bradesco_service.executar_protesto_api(nosso_numero, codigo_funcao)

            if resp.get("cdErro", 0) != 0:
                return {"sucesso": False, "erro": resp.get("msgErro", "Erro ao protestar")}

            label = "Negativação" if tipo == "negativacao" else "Protesto"

            create_log(
                consulta_id="BOLETO_PROTESTO",
                nivel="WARN",
                mensagem=f"{label} solicitado: {nosso_numero} por {usuario_id}",
                payload={
                    "nosso_numero": nosso_numero,
                    "tipo": tipo,
                    "codigo_funcao": codigo_funcao,
                    "tipo_alteracao": "PROTESTO",
                    "status_novo": STATUS_PROTESTO,
                    "origem": "MANUAL",
                    "alterado_por": usuario_id,
                }
            )

            return {"sucesso": True, "mensagem": f"{label} solicitado com sucesso"}

        except Exception as e:
            logger.error(f"[BoletoService] Erro ao protestar: {e}")
            return {"sucesso": False, "erro": str(e)}

    # ========================= CALCULATIONS =========================

    @staticmethod
    def calcular_juros_multa(
        valor_nominal: float,
        data_vencimento: date,
        percentual_juros_dia: float = 0.0333,
        percentual_multa: float = 2.0,
    ) -> dict:
        """Calculate updated amount with interest and penalty for overdue boletos."""
        hoje = date.today()
        if hoje <= data_vencimento:
            return {
                "dias_atraso": 0,
                "valor_juros": 0.0,
                "valor_multa": 0.0,
                "valor_total": valor_nominal,
            }

        dias_atraso = (hoje - data_vencimento).days
        valor_juros = round(valor_nominal * (percentual_juros_dia / 100) * dias_atraso, 2)
        valor_multa = round(valor_nominal * (percentual_multa / 100), 2)
        valor_total = round(valor_nominal + valor_juros + valor_multa, 2)

        return {
            "dias_atraso": dias_atraso,
            "valor_juros": valor_juros,
            "valor_multa": valor_multa,
            "valor_total": valor_total,
        }

    # ========================= STATISTICS =========================

    @staticmethod
    def calcular_estatisticas(boletos: list[dict]) -> dict:
        """Calculate billing statistics from a list of boletos."""
        if not boletos:
            return {
                "total": 0, "a_vencer": 0, "pagos": 0, "vencidos": 0,
                "valor_total": 0, "valor_recebido": 0, "valor_pendente": 0,
                "taxa_recebimento": 0.0,
            }

        total = len(boletos)
        pagos = sum(1 for b in boletos if b.get("status") in ("pago", "61"))
        vencidos = sum(1 for b in boletos if b.get("status") in ("vencido", "atraso"))
        a_vencer = total - pagos - vencidos

        valor_total = sum(float(b.get("valor", 0)) for b in boletos)
        valor_recebido = sum(float(b.get("valor", 0)) for b in boletos if b.get("status") in ("pago", "61"))
        valor_pendente = valor_total - valor_recebido
        taxa = (pagos / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "a_vencer": a_vencer,
            "pagos": pagos,
            "vencidos": vencidos,
            "valor_total": round(valor_total, 2),
            "valor_recebido": round(valor_recebido, 2),
            "valor_pendente": round(valor_pendente, 2),
            "taxa_recebimento": round(taxa, 1),
        }

    # ========================= VALIDATION =========================

    @staticmethod
    def validar_cpf_cnpj(doc: str) -> bool:
        """Validate CPF (11 digits) or CNPJ (14 digits)."""
        limpo = re.sub(r"\D", "", doc)
        if len(limpo) == 11:
            return BoletoService._validar_cpf(limpo)
        elif len(limpo) == 14:
            return BoletoService._validar_cnpj(limpo)
        return False

    @staticmethod
    def _validar_cpf(cpf: str) -> bool:
        if len(set(cpf)) == 1:
            return False
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[9]):
            return False
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        return resto == int(cpf[10])

    @staticmethod
    def _validar_cnpj(cnpj: str) -> bool:
        if len(set(cnpj)) == 1:
            return False
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        d1 = 0 if soma % 11 < 2 else 11 - (soma % 11)
        if d1 != int(cnpj[12]):
            return False
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        d2 = 0 if soma % 11 < 2 else 11 - (soma % 11)
        return d2 == int(cnpj[13])


boleto_service = BoletoService()
