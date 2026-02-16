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
from app.routes import empresas, consultas, dashboard, query, pdf
from app.services.scheduler import process_pending_queries, create_daily_schedules

# ─── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── APScheduler ─────────────────────────────────────────────────────

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle manager."""
    logger.info("🚀 IAudit starting up...")

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

    scheduler.start()
    logger.info(
        f"📅 Scheduler started: polling every {settings.scheduler_poll_interval_minutes}min, "
        f"daily at {settings.scheduler_daily_hour:02d}:{settings.scheduler_daily_minute:02d}"
    )

    yield

    # Shutdown
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
    }
