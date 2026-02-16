"""IAudit - Empresas API routes."""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Query

from app.database import (
    get_empresas,
    get_empresa_by_id,
    get_empresa_by_cnpj,
    create_empresa,
    update_empresa,
    delete_empresa,
    clear_all_empresas,
    create_consulta,
)
from app.models import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResponse,
    UploadResult,
    ForceQueryRequest,
)
from app.services.cnpj import validate_cnpj, clean_cnpj

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/empresas", tags=["Empresas"])


@router.get("", response_model=list[EmpresaResponse])
def list_empresas(
    ativo: bool | None = None,
    search: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List empresas with optional filters."""
    return get_empresas(ativo=ativo, search=search, limit=limit, offset=offset)


@router.get("/{empresa_id}", response_model=EmpresaResponse)
def get_empresa(empresa_id: str):
    """Get a single empresa by ID."""
    empresa = get_empresa_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return empresa


@router.post("", response_model=EmpresaResponse, status_code=201)
def create_empresa_route(data: EmpresaCreate):
    """Create a new empresa with CNPJ validation."""
    cnpj = clean_cnpj(data.cnpj)

    if not validate_cnpj(cnpj):
        raise HTTPException(status_code=400, detail=f"CNPJ inválido: {cnpj}")

    # Check duplicate
    existing = get_empresa_by_cnpj(cnpj)
    if existing:
        raise HTTPException(status_code=409, detail=f"CNPJ já cadastrado: {cnpj}")

    empresa_data = data.model_dump()
    empresa_data["cnpj"] = cnpj
    return create_empresa(empresa_data)


@router.put("/{empresa_id}", response_model=EmpresaResponse)
def update_empresa_route(empresa_id: str, data: EmpresaUpdate):
    """Update an empresa."""
    empresa = get_empresa_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    return update_empresa(empresa_id, update_data)


@router.delete("/{empresa_id}", status_code=204)
def delete_empresa_route(empresa_id: str):
    """Soft-delete (deactivate) an empresa."""
    empresa = get_empresa_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    delete_empresa(empresa_id)


@router.delete("/purge", status_code=204)
def purge_empresas_route():
    """Permanent hard-delete of ALL empresas."""
    try:
        clear_all_empresas()
    except Exception as e:
        logger.error(f"Purge failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{empresa_id}/force-query", status_code=201)
def force_query(empresa_id: str, request: ForceQueryRequest):
    """Force immediate consultation for an empresa."""
    empresa = get_empresa_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    now = datetime.now(timezone.utc).isoformat()
    created = []

    for tipo in request.tipos:
        consulta = create_consulta({
            "empresa_id": empresa_id,
            "tipo": tipo.value,
            "status": "agendada",
            "data_agendada": now,
            "tentativas": 0,
        })
        created.append(consulta)

    return {"message": f"{len(created)} consulta(s) agendada(s)", "consultas": created}


@router.post("/upload", response_model=UploadResult)
async def upload_csv(
    file: UploadFile = File(...),
    periodicidade: str = Query("mensal"),
    horario: str = Query("08:00:00"),
):
    """
    Upload CSV/Excel with empresa data.

    Expected columns: cnpj, razao_social, inscricao_estadual_pr (optional),
    email_notificacao (optional), whatsapp (optional)
    """
    result = UploadResult()

    try:
        content = await file.read()
        filename = file.filename or "upload.csv"

        if filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            # Try various CSV encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise HTTPException(status_code=400, detail="Encoding do arquivo não reconhecido")

        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        if "cnpj" not in df.columns:
            raise HTTPException(status_code=400, detail="Coluna 'cnpj' não encontrada no arquivo")

        if "razao_social" not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Coluna 'razao_social' não encontrada no arquivo",
            )

        result.total = len(df)

        for _, row in df.iterrows():
            cnpj_raw = str(row.get("cnpj", ""))
            cnpj = clean_cnpj(cnpj_raw)
            razao = str(row.get("razao_social", "")).strip()

            if not cnpj or not razao:
                result.invalidas += 1
                result.erros.append(f"Linha vazia: CNPJ={cnpj_raw}")
                continue

            if not validate_cnpj(cnpj):
                result.invalidas += 1
                result.erros.append(f"CNPJ inválido: {cnpj_raw}")
                continue

            # Check duplicate
            existing = get_empresa_by_cnpj(cnpj)
            if existing:
                result.duplicadas += 1
                continue

            # Create empresa
            try:
                empresa_data = {
                    "cnpj": cnpj,
                    "razao_social": razao,
                    "inscricao_estadual_pr": str(row.get("inscricao_estadual_pr", "")).strip() or None,
                    "email_notificacao": str(row.get("email_notificacao", "")).strip() or None,
                    "whatsapp": str(row.get("whatsapp", "")).strip() or None,
                    "periodicidade": periodicidade,
                    "horario": horario,
                    "ativo": True,
                }
                create_empresa(empresa_data)
                result.criadas += 1
            except Exception as e:
                result.erros.append(f"Erro ao salvar {cnpj}: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")

    return result
