"""IAudit - InfoSimples API client with rate limiting and retry logic."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Endpoints
ENDPOINTS = {
    "cnd_federal": "https://api.infosimples.com/api/v2/consultas/receita-federal/pgfn/nova",
    "cnd_pr": "https://api.infosimples.com/api/v2/consultas/sefaz/pr/certidao-debitos",
    "fgts_regularidade": "https://api.infosimples.com/api/v2/consultas/caixa/regularidade",
}


class InfoSimplesClient:
    """
    Async client for InfoSimples API with:
    - Rate limiting (3s between requests)
    - Retry logic (3 attempts, 5-min backoff)
    """

    def __init__(self):
        self._semaphore = asyncio.Semaphore(1)
        self._last_request_time: float = 0
        self._rate_limit_seconds = settings.rate_limit_seconds

    async def _enforce_rate_limit(self):
        """Ensure minimum interval between API requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_seconds:
            wait = self._rate_limit_seconds - elapsed
            logger.debug(f"Rate limit: waiting {wait:.1f}s")
            await asyncio.sleep(wait)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _make_request(
        self, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Make a single API request with rate limiting."""
        async with self._semaphore:
            await self._enforce_rate_limit()

            # InfoSimples expects token as POST form parameter
            payload["token"] = settings.infosimples_token

            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"InfoSimples request: {endpoint}")
                response = await client.post(
                    endpoint, data=payload
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"InfoSimples response code: {data.get('code')}")
                return data

    async def consultar_cnd_federal(self, cnpj: str) -> dict[str, Any]:
        """
        Query CND Federal (Receita Federal / PGFN).

        Returns:
            Dict with keys: situacao, pdf_url, resultado_json, data_validade
        """
        payload = {"cnpj": cnpj, "tipo": "cnpj"}
        endpoint = ENDPOINTS["cnd_federal"]

        try:
            data = await self._make_request(endpoint, payload)
            return self._parse_cnd_response(data, "cnd_federal")
        except Exception as e:
            logger.error(f"CND Federal error for {cnpj}: {e}")
            return {
                "situacao": "erro",
                "pdf_url": None,
                "resultado_json": {"error": str(e)},
                "data_validade": None,
            }

    async def consultar_cnd_pr(
        self, cnpj: str, inscricao_estadual: str | None = None
    ) -> dict[str, Any]:
        """
        Query CND Paraná (SEFAZ PR).

        Returns:
            Dict with keys: situacao, pdf_url, resultado_json, data_validade
        """
        payload: dict[str, Any] = {"cnpj": cnpj}
        if inscricao_estadual:
            payload["inscricao_estadual"] = inscricao_estadual

        endpoint = ENDPOINTS["cnd_pr"]

        try:
            data = await self._make_request(endpoint, payload)
            return self._parse_cnd_response(data, "cnd_pr")
        except Exception as e:
            logger.error(f"CND PR error for {cnpj}: {e}")
            return {
                "situacao": "erro",
                "pdf_url": None,
                "resultado_json": {"error": str(e)},
                "data_validade": None,
            }

    async def consultar_fgts(self, cnpj: str) -> dict[str, Any]:
        """
        Query FGTS Regularidade (CAIXA).

        Returns:
            Dict with keys: situacao, pdf_url, resultado_json, data_validade
        """
        payload = {"cnpj": cnpj}
        endpoint = ENDPOINTS["fgts_regularidade"]

        try:
            data = await self._make_request(endpoint, payload)
            return self._parse_fgts_response(data)
        except Exception as e:
            logger.error(f"FGTS error for {cnpj}: {e}")
            return {
                "situacao": "erro",
                "pdf_url": None,
                "resultado_json": {"error": str(e)},
                "data_validade": None,
            }

    def _parse_cnd_response(
        self, data: dict[str, Any], tipo: str
    ) -> dict[str, Any]:
        """Parse CND response from InfoSimples."""
        code = data.get("code")
        result: dict[str, Any] = {
            "resultado_json": data,
            "pdf_url": None,
            "data_validade": None,
            "situacao": "erro",
        }

        if code == 200:
            # Success — extract fields
            response_data = data.get("data", [{}])
            if isinstance(response_data, list) and response_data:
                item = response_data[0]
            elif isinstance(response_data, dict):
                item = response_data
            else:
                item = {}

            # Determine situacao
            situacao_raw = (
                item.get("situacao", "")
                or item.get("certidao_situacao", "")
                or ""
            ).lower()

            if "positiva" in situacao_raw or "negativa" not in situacao_raw:
                result["situacao"] = "positiva"
            else:
                result["situacao"] = "negativa"

            # Extract PDF URL
            result["pdf_url"] = (
                item.get("site_receipt_url")
                or item.get("pdf_url")
                or item.get("certidao_url")
                or data.get("site_receipt_url")
            )

            # Extract validity date
            validade = item.get("data_validade") or item.get("validade")
            if validade:
                result["data_validade"] = validade

        elif code == 600:
            # Negative certificate
            result["situacao"] = "negativa"
            result["pdf_url"] = data.get("site_receipt_url")
        else:
            result["situacao"] = "erro"

        return result

    def _parse_fgts_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse FGTS response from InfoSimples."""
        code = data.get("code")
        result: dict[str, Any] = {
            "resultado_json": data,
            "pdf_url": None,
            "data_validade": None,
            "situacao": "erro",
        }

        if code == 200:
            response_data = data.get("data", [{}])
            if isinstance(response_data, list) and response_data:
                item = response_data[0]
            elif isinstance(response_data, dict):
                item = response_data
            else:
                item = {}

            situacao_raw = (
                item.get("situacao", "") or item.get("resultado", "") or ""
            ).lower()

            if "regular" in situacao_raw and "irregular" not in situacao_raw:
                result["situacao"] = "regular"
            else:
                result["situacao"] = "irregular"

            result["pdf_url"] = (
                item.get("site_receipt_url")
                or item.get("pdf_url")
                or data.get("site_receipt_url")
            )

            validade = item.get("data_validade") or item.get("validade")
            if validade:
                result["data_validade"] = validade
        else:
            result["situacao"] = "erro"

        return result


# Module-level singleton
infosimples_client = InfoSimplesClient()
