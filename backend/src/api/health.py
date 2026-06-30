"""Health check, settings introspection, and integration status endpoints."""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter

from src.config.settings import get_settings
from src.integrations.registry import IntegrationRegistry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
async def health() -> dict[str, Any]:
    """Liveness + readiness check."""
    settings = get_settings()
    checks: dict[str, Any] = {}

    # DB check
    try:
        from src.data.supabase import get_supabase_client
        client = get_supabase_client()
        await client.table("users").select("count").limit(1).execute()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"unavailable: {exc}"

    # LLM check
    try:
        from src.llm.factory import get_llm
        llm = get_llm("classification")
        checks["llm"] = f"ok ({settings.get_task_provider('classification')})"
    except Exception as exc:
        checks["llm"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" or v.startswith("ok") for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "checks": checks,
        "environment": settings.environment,
        "version": settings.app.get("version", "unknown"),
    }


@router.get("/config/summary")
async def config_summary() -> dict[str, Any]:
    """
    Return a non-sensitive config summary for UI display and debugging.
    Secrets and API keys are never returned.
    """
    settings = get_settings()
    return {
        "llm": {
            "task_providers": settings.llm.get("task_providers", {}),
            "available_providers": list(settings.llm.get("providers", {}).keys()),
            "fallback_chain": settings.get_fallback_chain(),
        },
        "graph": {
            "checkpointer": settings.graph.get("checkpointer"),
            "max_iterations": settings.graph.get("max_iterations"),
        },
        "tutor": {
            "topics": [t["id"] for t in settings.tutor.get("topics", [])],
            "active_decorators": settings.get_active_decorators(),
        },
        "integrations": {
            "enabled": settings.get_enabled_integrations(),
            "active": IntegrationRegistry.list_active(),
        },
        "auth_mode": settings.auth_mode,
        "environment": settings.environment,
    }


@router.get("/integrations")
async def list_integrations() -> dict[str, Any]:
    """List all registered integrations and their status."""
    return {
        "registered": IntegrationRegistry.list_registered(),
        "active": IntegrationRegistry.list_active(),
    }


@router.post("/integrations/{name}/reload")
async def reload_integration(name: str) -> dict[str, str]:
    """Hot-reload a specific integration without restarting the server."""
    try:
        await IntegrationRegistry._load(name)
        return {"status": "reloaded", "name": name}
    except Exception as exc:
        return {"status": "error", "name": name, "detail": str(exc)}
