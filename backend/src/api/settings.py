"""Settings management API — update decorators, topic, and notification channels at runtime."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.deps import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


class DecoratorUpdate(BaseModel):
    active_decorators: list[str]


class TopicUpdate(BaseModel):
    topic: str
    subtopic: str | None = None


@router.get("")
async def get_settings_summary(user: dict = Depends(get_current_user)) -> dict[str, Any]:
    """Return current runtime-configurable settings for the authenticated user."""
    from src.config.settings import get_settings
    from src.graph.decorators.registry import DecoratorRegistry

    settings = get_settings()
    return {
        "active_decorators": settings.get_active_decorators(),
        "available_decorators": list(settings.decorators_cfg.get("available", {}).keys()),
        "registered_decorators": DecoratorRegistry.list_registered(),
        "topics": settings.tutor.get("topics", []),
        "active_provider": {
            task: settings.get_task_provider(task)
            for task in ["chat", "planning", "evaluation", "classification"]
        },
        "enabled_integrations": settings.get_enabled_integrations(),
    }
