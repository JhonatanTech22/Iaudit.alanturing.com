"""IAudit - FastAPI application with APScheduler."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import empresas, consultas, dashboard, query, pdf, cobrancas, comunicacoes
from app.services.scheduler import process_pending_queries, create_daily_schedules
from app.services.monitoring import monitor_boletos
from app.services.billing import billing_service
from app.services.boleto_scheduler import check_boleto_vencimentos
from app.services.notification_queue import notification_queue

# ─── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── APScheduler ─────────────────────────────────────────────────────

scheduler = AsyncIOScheduler()

_queue_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle manager."""
    global _queue_task

    logger.info("🚀 IAudit starting up...")

    # ── Start Notification Queue Worker ──────────────────────────────
    _queue_task = asyncio.create_task(notification_queue.start_worker())
    logger.info("📬 Notification queue worker started.")

    # Job 1: Process pending queries every N minutes
    scheduler.add_job(
        process_pending_queries,
        trigger=IntervalTrigger(minutes=settings.scheduler_poll_interval_minutes),
        id="process_pending",
        name="Process Pending Queries",
        replace_existing=True,
    )

    # Job 2: Create daily schedules
    scheduler.add_job(
        create_daily_schedules,
        trigger=CronTrigger(
            hour=settings.scheduler_daily_hour,
            minute=settings.scheduler_daily_minute,
        ),
        id="daily_schedules",
        name="Create Daily Schedules",
        replace_existing=True,
    )

    # Job 3: Monitor Boletos Status (Hourly)
    scheduler.add_job(
        monitor_boletos,
        trigger=IntervalTrigger(minutes=60),
        id="monitor_boletos",
        name="Monitor Boletos Status",
        replace_existing=True,
    )

    # Job 4: Process Recurring Billing (Daily at 06:00)
    scheduler.add_job(
        billing_service.process_recurring_billing,
        trigger=CronTrigger(hour=6, minute=0),
        id="recurring_billing",
        name="Process Recurring Billing",
        replace_existing=True,
    )

    # Job 5: D-1 / D+1 Vencimento Alerts (Daily at configured hour)
    scheduler.add_job(
        check_boleto_vencimentos,
        trigger=CronTrigger(
            hour=settings.notification_vencimento_hour,
            minute=0,
        ),
        id="boleto_vencimentos",
        name="Check Boleto Vencimentos (D-1/D+1)",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"📅 Scheduler started: polling every {settings.scheduler_poll_interval_minutes}min, "
        f"daily at {settings.scheduler_daily_hour:02d}:{settings.scheduler_daily_minute:02d}, "
        f"vencimento check at {settings.notification_vencimento_hour:02d}:00"
    )

    yield

    # Shutdown
    notification_queue.stop_worker()
    if _queue_task:
        _queue_task.cancel()
    scheduler.shutdown(wait=False)
    logger.info("🛑 IAudit shutting down...")


# ─── FastAPI App ─────────────────────────────────────────────────────

app = FastAPI(
    title="IAudit API",
    description="Sistema de Automação Fiscal — Monitoramento de CND e FGTS",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(empresas.router)
app.include_router(consultas.router)
app.include_router(dashboard.router)
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["pdf"])
app.include_router(cobrancas.router, prefix="/api/cobranca", tags=["cobranca"])
app.include_router(comunicacoes.router)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0",
    }


@app.get("/api/health", tags=["Health"])
def api_health():
    """API health check with scheduler status."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })

    return {
        "status": "ok",
        "scheduler_running": scheduler.running,
        "jobs": jobs,
        "notification_queue": notification_queue.stats,
    }
