"""IAudit - Consultas API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.database import get_consultas, get_consulta_by_id
from app.models import ConsultaResponse

router = APIRouter(prefix="/api/consultas", tags=["Consultas"])


@router.get("", response_model=list[ConsultaResponse])
def list_consultas(
    empresa_id: str | None = None,
    tipo: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List consultas with optional filters."""
    return get_consultas(
        empresa_id=empresa_id,
        tipo=tipo,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{consulta_id}", response_model=ConsultaResponse)
def get_consulta(consulta_id: str):
    """Get a single consulta with full details."""
    consulta = get_consulta_by_id(consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return consulta
