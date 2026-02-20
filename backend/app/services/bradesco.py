"""IAudit - Bradesco API Integration (v1.7.1).

Features:
  - OAuth2 via JWT Profile (RS256)
  - TLS 1.2 with mandated cipher suite
  - Boleto: register, register-qr-code, alter, cancel (estorno), consult
  - Notification triggers on success events
"""

from __future__ import annotations

import jwt
import ssl
import time
import uuid
import logging
import asyncio
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.services.notifications import send_boleto_notification

logger = logging.getLogger(__name__)

# ─── URLs ────────────────────────────────────────────────────────────

SANDBOX_URL = "https://proxy.api.prebanco.com.br"
PRODUCTION_URL = "https://openapi.bradesco.com.br"


# ─── TLS 1.2 Context ────────────────────────────────────────────────

def _create_tls_context() -> ssl.SSLContext:
    """Build SSLContext forcing TLS 1.2 with Bradesco-mandated cipher.

    Cipher: TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
    Reference: Manual Bradesco API v1.7.1, Seção de Segurança.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    ctx.set_ciphers("ECDHE-RSA-AES128-GCM-SHA256")
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED

    # Load Bradesco client certificate if configured
    if settings.bradesco_certificate_path and settings.bradesco_private_key_path:
        try:
            ctx.load_cert_chain(
                certfile=settings.bradesco_certificate_path,
                keyfile=settings.bradesco_private_key_path,
            )
        except Exception as e:
            logger.warning(f"Could not load Bradesco cert chain: {e}")

    return ctx


def _build_http_client() -> httpx.AsyncClient:
    """Create an httpx client with TLS 1.2 enforcement."""
    tls_ctx = _create_tls_context()
    return httpx.AsyncClient(
        verify=tls_ctx,
        timeout=httpx.Timeout(30.0, connect=10.0),
    )


# ═══════════════════════════════════════════════════════════════════════

class BradescoService:
    """Bradesco banking API client."""

    def __init__(self):
        self.base_url = SANDBOX_URL if settings.bradesco_sandbox else PRODUCTION_URL
        self._token: str | None = None
        self._token_expires_at: float = 0

    # ── Auth ──────────────────────────────────────────────────────────

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token via JWT Profile (RS256)."""
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        if not settings.bradesco_client_id or not settings.bradesco_private_key_path:
            logger.warning("Bradesco credentials not fully configured. Using MOCK.")
            return "MOCK_TOKEN"

        now = int(time.time())
        claims = {
            "aud": f"{self.base_url}/auth/server/v1.1/token",
            "sub": settings.bradesco_client_id,
            "iat": now,
            "exp": now + 3600,
            "jti": str(uuid.uuid4()),
        }

        try:
            with open(settings.bradesco_private_key_path, "r") as f:
                private_key = f.read()

            signed_jwt = jwt.encode(claims, private_key, algorithm="RS256")

            async with _build_http_client() as client:
                data = {
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": signed_jwt,
                }
                resp = await client.post(
                    f"{self.base_url}/auth/server/v1.1/token", data=data
                )
                resp.raise_for_status()
                token_data = resp.json()
                self._token = token_data["access_token"]
                self._token_expires_at = now + int(
                    token_data.get("expires_in", 3600)
                )
                return self._token
        except Exception as e:
            logger.error(f"Failed to get Bradesco access token: {e}")
            raise

    def _auth_headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    # ── Register Boleto ──────────────────────────────────────────────

    async def register_boleto(
        self,
        boleto_data: dict,
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
    ) -> dict:
        """Register a boleto and trigger 'emitido' notification on success."""
        token = await self._get_access_token()

        negociacao = settings.bradesco_negociacao.zfill(18)

        payload = {
            "nuNegociacao": negociacao,
            "tpAcessorio": "10",
            "acessEsc10": settings.bradesco_acess_esc10,
            "nuCliente": boleto_data.get("nuFatura"),
            "vlNominalTitulo": str(boleto_data.get("vlNominal")),
            "dtVencimentoTitulo": str(boleto_data.get("dataVencimento")),
            "pagador": {
                "nome": boleto_data.get("pagador_nome"),
                "documento": boleto_data.get("pagador_documento"),
                "endereco": boleto_data.get("pagador_endereco"),
                "cep": boleto_data.get("pagador_cep"),
                "uf": boleto_data.get("pagador_uf"),
                "cidade": boleto_data.get("pagador_cidade"),
                "bairro": boleto_data.get("pagador_bairro"),
            },
            "prJuros": boleto_data.get("prJuros", "0"),
            "prMulta": boleto_data.get("prMulta", "0"),
        }

        endpoint = "/v1/boleto/registrar"

        # MOCK MODE
        if token == "MOCK_TOKEN":
            logger.info("MOCK MODE: Simulated Bradesco register success.")
            nosso_num = str(int(time.time()))[-10:]
            linha = f"2379{nosso_num}9000000000000050000000000"

            # Trigger notification even in mock mode
            if recipient_email or recipient_phone:
                notif_data = {
                    "nomeSacado": boleto_data.get("pagador_nome"),
                    "valorNominal": boleto_data.get("vlNominal"),
                    "dataVencimento": boleto_data.get("dataVencimento"),
                    "linhaDigitavel": linha,
                    "qrCodePix": "",
                    "linkPdfBoleto": f"{settings.backend_url}/api/boleto/pdf/{nosso_num}",
                }
                asyncio.create_task(
                    send_boleto_notification(
                        "emitido", notif_data, recipient_email, recipient_phone
                    )
                )
                logger.info(f"MOCK: Notification dispatched to email={recipient_email}, phone={recipient_phone}")

            return {
                "cdErro": 0,
                "msgErro": "Sucesso (Mock)",
                "nuNossoNumero": nosso_num,
                "linhaDigitavel": linha,
                "cdSituacaoTitulo": "01",
                "listaRegistro": [
                    {"linhaDigitavel": linha}
                ],
            }

        async with _build_http_client() as client:
            try:
                resp = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=self._auth_headers(token),
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Bradesco API Error: {e.response.text}")
                return {"cdErro": e.response.status_code, "msgErro": e.response.text}

            data = resp.json()

            if data.get("cdErro", 0) != 0:
                logger.error(f"Bradesco business error: {data}")
                return data

            # Extract key fields
            linha_digitavel = data.get("linhaDigitavel", "")
            if not linha_digitavel and "listaRegistro" in data:
                linha_digitavel = data["listaRegistro"][0].get("linhaDigitavel", "")

            cd_barras = data.get("cdBarras", "")
            emv_qr = data.get("emv", "")  # QR Code Pix

            # Trigger 'emitido' notification
            notif_data = {
                "nomeSacado": boleto_data.get("pagador_nome"),
                "valorNominal": boleto_data.get("vlNominal"),
                "dataVencimento": boleto_data.get("dataVencimento"),
                "linhaDigitavel": linha_digitavel,
                "qrCodePix": emv_qr,
                "linkPdfBoleto": (
                    f"{settings.backend_url}/api/boleto/pdf/"
                    f"{boleto_data.get('nuFatura')}"
                ),
            }

            if recipient_email or recipient_phone:
                asyncio.create_task(
                    send_boleto_notification(
                        "emitido", notif_data, recipient_email, recipient_phone
                    )
                )

            return data

    # ── Register Boleto with QR Code ─────────────────────────────────

    async def register_boleto_qr_code(self, boleto_data: dict) -> dict:
        """Register via /v1/boleto-hibrido/registrar-boleto (QR + Linha)."""
        token = await self._get_access_token()
        endpoint = "/v1/boleto-hibrido/registrar-boleto"

        if token == "MOCK_TOKEN":
            return {"cdErro": 0, "msgErro": "Sucesso (Mock QR)"}

        async with _build_http_client() as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json=boleto_data,
                headers=self._auth_headers(token),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Alter Boleto ─────────────────────────────────────────────────

    async def alter_boleto(self, boleto_data: dict) -> dict:
        """Alter boleto data (e.g. extension). PUT /v1/boleto/titulo-alterar."""
        token = await self._get_access_token()
        endpoint = "/v1/boleto/titulo-alterar"

        if token == "MOCK_TOKEN":
            return {"cdErro": 0, "msgErro": "Alteração simulada (Mock)"}

        async with _build_http_client() as client:
            resp = await client.put(
                f"{self.base_url}{endpoint}",
                json=boleto_data,
                headers=self._auth_headers(token),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Cancel / Estorno ─────────────────────────────────────────────

    async def cancel_boleto(
        self,
        nosso_numero: str,
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
        boleto_data: dict | None = None,
    ) -> dict:
        """Estornar (reactivate) boleto via /v1/boleto/titulo-estornar.

        On success (CBTT0710), triggers 'reativado' notification.
        """
        token = await self._get_access_token()

        payload = {
            "nuNegociacao": settings.bradesco_negociacao.zfill(18),
            "nuNossoNumero": nosso_numero,
        }

        endpoint = "/v1/boleto/titulo-estornar"

        if token == "MOCK_TOKEN":
            logger.info("MOCK MODE: Simulated estorno success (CBTT0710).")
            result = {
                "cdErro": 0,
                "msgErro": "Estorno simulado (Mock)",
                "cdRetorno": "CBTT0710",
            }
            # Fire notification
            if (recipient_email or recipient_phone) and boleto_data:
                asyncio.create_task(
                    send_boleto_notification(
                        "reativado",
                        {
                            "nomeSacado": boleto_data.get("pagador_nome", "Cliente"),
                            "valorNominal": boleto_data.get("vlNominal", 0),
                            "dataVencimento": boleto_data.get("dataVencimento", ""),
                            "linhaDigitavel": boleto_data.get("linhaDigitavel", ""),
                            "linkPdfBoleto": (
                                f"{settings.backend_url}/api/boleto/pdf/{nosso_numero}"
                            ),
                        },
                        recipient_email,
                        recipient_phone,
                    )
                )
            return result

        async with _build_http_client() as client:
            try:
                resp = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=self._auth_headers(token),
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Estorno API Error: {e.response.text}")
                return {"cdErro": e.response.status_code, "msgErro": e.response.text}

            data = resp.json()

            # Check for success code CBTT0710
            if data.get("cdRetorno") == "CBTT0710" or data.get("cdErro", 0) == 0:
                logger.info(f"Estorno success for {nosso_numero}")

                if (recipient_email or recipient_phone) and boleto_data:
                    asyncio.create_task(
                        send_boleto_notification(
                            "reativado",
                            {
                                "nomeSacado": boleto_data.get("pagador_nome", ""),
                                "valorNominal": boleto_data.get("vlNominal", 0),
                                "dataVencimento": boleto_data.get(
                                    "dataVencimento", ""
                                ),
                                "linhaDigitavel": boleto_data.get(
                                    "linhaDigitavel", ""
                                ),
                                "linkPdfBoleto": (
                                    f"{settings.backend_url}/api/boleto/pdf/"
                                    f"{nosso_numero}"
                                ),
                            },
                            recipient_email,
                            recipient_phone,
                        )
                    )

            return data

    # ── Baixar (Write-off, different from Estorno) ───────────────────

    async def baixar_boleto_api(self, nosso_numero: str, motivo: str) -> dict:
        """Request write-off. POST /v1/boleto/titulo-baixar."""
        token = await self._get_access_token()

        payload = {
            "nuNegociacao": settings.bradesco_negociacao.zfill(18),
            "nuNossoNumero": nosso_numero,
            "cdMotivoBaixa": motivo,
        }

        endpoint = "/v1/boleto/titulo-baixar"

        if token == "MOCK_TOKEN":
            return {"cdErro": 0, "msgErro": "Baixa simulada (Mock)"}

        async with _build_http_client() as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self._auth_headers(token),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Protest ──────────────────────────────────────────────────────

    async def executar_protesto_api(
        self, nosso_numero: str, codigo_funcao: str
    ) -> dict:
        """Request protest or credit bureau. POST /v1/boleto/titulo-protestar."""
        token = await self._get_access_token()

        payload = {
            "nuNegociacao": settings.bradesco_negociacao.zfill(18),
            "nuNossoNumero": nosso_numero,
            "cdFuncao": codigo_funcao,
        }

        endpoint = "/v1/boleto/titulo-protestar"

        if token == "MOCK_TOKEN":
            return {"cdErro": 0, "msgErro": "Protesto simulado (Mock)"}

        async with _build_http_client() as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self._auth_headers(token),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Consult Status ───────────────────────────────────────────────

    async def consult_status(self, nosso_numero: str) -> tuple[str, dict]:
        """Query current status. Maps Bradesco codes to internal status."""
        token = await self._get_access_token()

        payload = {
            "nuNegociacao": settings.bradesco_negociacao.zfill(18),
            "nuNossoNumero": nosso_numero,
        }

        endpoint = "/v1/boleto/titulo-consultar"

        if token == "MOCK_TOKEN":
            return "emitido", {"cdSituacaoTitulo": "01", "mock": True}

        async with _build_http_client() as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self._auth_headers(token),
            )
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return "erro", {}

            # Status code extraction
            status_codigo = str(data.get("cdSituacaoTitulo", ""))

            if "listaTitulo" in data and len(data["listaTitulo"]) > 0:
                item = data["listaTitulo"][0]
                status_codigo = str(item.get("cdSituacaoTitulo", ""))

            # Bradesco status mapping
            # 13 = Pago no dia, 61 = Baixa por Título Pago, 06 = Liquidado
            if status_codigo in ("13", "61", "06"):
                return "pago", data
            elif status_codigo == "02":  # Baixado / Devolvido
                return "baixado", data

            return "emitido", data


# ─── Singleton ───────────────────────────────────────────────────────

bradesco_service = BradescoService()
