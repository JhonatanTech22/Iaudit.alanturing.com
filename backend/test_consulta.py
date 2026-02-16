"""IAudit - Teste de Consulta InfoSimples (token como parametro POST)."""

import asyncio
import json
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

# Novo token fornecido pelo usuario
TOKEN = "hMCSftuB24pA60fX2T2lSwwmDw7Wr7PRq7aM6Dcj"

ENDPOINTS = {
    "cnd_federal": {
        "url": "https://api.infosimples.com/api/v2/consultas/receita-federal/pgfn/nova",
        "label": "CND Federal (Receita Federal / PGFN)",
    },
    "cnd_pr": {
        "url": "https://api.infosimples.com/api/v2/consultas/sefaz/pr/certidao-debitos",
        "label": "CND Parana (SEFAZ PR)",
    },
}


async def consultar(tipo, cnpj):
    endpoint = ENDPOINTS[tipo]
    print("")
    print("=" * 60)
    print("  Consultando: " + endpoint["label"])
    print("  CNPJ: " + cnpj)
    print("=" * 60)

    # Token vai como parametro do body, NAO como header Bearer
    payload = {
        "token": TOKEN,
        "cnpj": cnpj,
    }
    if tipo == "cnd_federal":
        payload["tipo"] = "cnpj"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("  Enviando requisicao (token como parametro POST)...")

            # Tentar como form-encoded
            response = await client.post(
                endpoint["url"],
                data=payload,
                timeout=120.0,
            )

            status_code = response.status_code
            print("  HTTP Status: " + str(status_code))

            data = response.json()
            code = data.get("code")
            code_message = data.get("code_message", "")
            print("  API Code: " + str(code) + " - " + code_message)

            client_name = ""
            if data.get("header"):
                client_name = data["header"].get("client_name", "") or ""
                token_name = data["header"].get("token_name", "") or ""
                if client_name:
                    print("  Cliente: " + client_name)
                if token_name:
                    print("  Token: " + token_name)

            if data.get("data"):
                print("")
                print("  DADOS RETORNADOS:")
                items = data["data"]
                if isinstance(items, list):
                    for i, item in enumerate(items):
                        print("  --- Item " + str(i + 1) + " ---")
                        for key, value in item.items():
                            if key not in ("site_receipt", "extra"):
                                val_str = str(value)
                                if len(val_str) > 300:
                                    val_str = val_str[:300] + "..."
                                print("    " + key + ": " + val_str)
                elif isinstance(items, dict):
                    for key, value in items.items():
                        if key not in ("site_receipt", "extra"):
                            val_str = str(value)
                            if len(val_str) > 300:
                                val_str = val_str[:300] + "..."
                            print("    " + key + ": " + val_str)

            if data.get("site_receipts"):
                print("")
                print("  PDFs/RECEIPTS:")
                for sr in data["site_receipts"]:
                    if isinstance(sr, dict):
                        print("    URL: " + sr.get("url", "N/A"))
                    else:
                        print("    " + str(sr))

            if data.get("errors"):
                print("  Erros: " + str(data["errors"]))

            if code == 200:
                print("")
                print("  >>> CONSULTA REALIZADA COM SUCESSO! <<<")
            elif code == 601:
                print("")
                print("  >>> TOKEN INVALIDO <<<")
            else:
                print("  Codigo: " + str(code))

            filename = "resultado_" + tipo + "_" + cnpj + ".json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("  Salvo em: " + filename)

            return data

    except httpx.TimeoutException:
        print("  TIMEOUT: requisicao excedeu 120 segundos")
    except Exception as e:
        print("  ERRO: " + str(e))
    return None


async def main():
    cnpj = "33000167000101"
    if len(sys.argv) > 1:
        cnpj = sys.argv[1].replace(".", "").replace("/", "").replace("-", "")

    print("")
    print("=" * 60)
    print("  IAudit - Teste de Consulta API InfoSimples")
    print("  CNPJ: " + cnpj)
    print("  Token: " + TOKEN[:8] + "...")
    print("=" * 60)

    result1 = await consultar("cnd_federal", cnpj)

    print("")
    print("  Aguardando 3s (rate limit)...")
    await asyncio.sleep(3)

    result2 = await consultar("cnd_pr", cnpj)

    print("")
    print("=" * 60)
    print("  Testes finalizados!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
