"""IAudit - Dashboard API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.database import (
    count_empresas,
    count_consultas_hoje,
    count_alertas_ativos,
    rpc_consultas_por_dia,
    rpc_alertas_ativos,
    rpc_proximas_consultas,
)
from app.models import DashboardStats, ChartData, AlertItem, UpcomingItem

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats():
    """Get dashboard KPI statistics."""
    total = count_empresas()
    ativas = count_empresas(ativo=True)
    hoje = count_consultas_hoje()
    alertas = count_alertas_ativos()

    # Calculate success rate
    taxa = 0.0
    if total > 0:
        try:
            chart = rpc_consultas_por_dia(7)
            total_queries = sum(r.get("total", 0) for r in chart)
            total_success = sum(r.get("sucessos", 0) for r in chart)
            if total_queries > 0:
                taxa = round((total_success / total_queries) * 100, 1)
        except Exception:
            pass

    return DashboardStats(
        total_empresas=total,
        empresas_ativas=ativas,
        consultas_hoje=hoje,
        alertas_ativos=alertas,
        taxa_sucesso=taxa,
    )


@router.get("/chart", response_model=list[ChartData])
def get_chart(dias: int = Query(7, ge=1, le=30)):
    """Get consultation stats per day for charting."""
    data = rpc_consultas_por_dia(dias)
    return [
        ChartData(
            data=str(r.get("data", "")),
            total=r.get("total", 0),
            sucessos=r.get("sucessos", 0),
            erros=r.get("erros", 0),
        )
        for r in data
    ]


@router.get("/alerts", response_model=list[AlertItem])
def get_alerts(limite: int = Query(20, ge=1, le=100)):
    """Get active alerts (negative CND, irregular FGTS)."""
    data = rpc_alertas_ativos(limite)
    return [
        AlertItem(
            consulta_id=str(r.get("consulta_id", "")),
            cnpj=r.get("cnpj", ""),
            razao_social=r.get("razao_social", ""),
            tipo=r.get("tipo", ""),
            situacao=r.get("situacao", ""),
            data_execucao=str(r.get("data_execucao", "")),
        )
        for r in data
    ]


@router.get("/upcoming", response_model=list[UpcomingItem])
def get_upcoming(limite: int = Query(10, ge=1, le=50)):
    """Get upcoming scheduled consultations."""
    data = rpc_proximas_consultas(limite)
    return [
        UpcomingItem(
            consulta_id=str(r.get("consulta_id", "")),
            cnpj=r.get("cnpj", ""),
            razao_social=r.get("razao_social", ""),
            tipo=r.get("tipo", ""),
            data_agendada=str(r.get("data_agendada", "")),
        )
        for r in data
    ]
