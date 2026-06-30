"""
FastAPI application entry point.

Startup sequence:
  1. Configure structured logging
  2. Initialise Supabase client
  3. Load enabled integrations
  4. Pre-compile LangGraph (warms the cache)
  5. Mount API routers
  6. Configure CORS

All behaviour is driven by config.yaml — no hardcoded values here.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.config.settings import get_settings

# ── Logging ───────────────────────────────────────────────────────────────────

def _configure_logging(log_level: str) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if log_level == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    )
    logging.basicConfig(level=log_level.upper(), stream=sys.stdout)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    _configure_logging(settings.log_level)

    logger = structlog.get_logger()
    logger.info(
        "Starting PersonalAITutor",
        environment=settings.environment,
        auth_mode=settings.auth_mode,
    )

    # Supabase
    try:
        from src.data.supabase import init_supabase
        await init_supabase()
    except Exception as exc:
        logger.warning("Supabase init failed (continuing without persistence)", error=str(exc))

    # Integration bus
    try:
        from src.integrations.registry import IntegrationRegistry
        await IntegrationRegistry.load_enabled()
    except Exception as exc:
        logger.warning("Integration bus init error", error=str(exc))

    # Pre-compile LangGraph (warms lru_cache)
    try:
        from src.graph.graph import build_graph
        build_graph()
        logger.info("LangGraph compiled and ready")
    except Exception as exc:
        logger.error("LangGraph compilation failed", error=str(exc))

    yield  # Application running

    # Shutdown
    logger.info("Shutting down PersonalAITutor")
    try:
        from src.integrations.registry import IntegrationRegistry
        await IntegrationRegistry.shutdown_all()
    except Exception as exc:
        logger.warning("Integration shutdown error", error=str(exc))


# ── Application ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app.get("name", "PersonalAITutor"),
        version=settings.app.get("version", "0.1.0"),
        description="Production-grade personal AI tutor with LangGraph + FastAPI",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Prometheus metrics ────────────────────────────────────────────────────
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # ── Routers ───────────────────────────────────────────────────────────────
    from src.api.health import router as health_router
    from src.api.progress import router as progress_router
    from src.api.settings import router as settings_router
    from src.api.tutor import router as tutor_router

    app.include_router(tutor_router)
    app.include_router(health_router)
    app.include_router(settings_router)
    app.include_router(progress_router)

    return app


app = create_app()
