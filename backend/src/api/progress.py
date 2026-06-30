"""Progress tracking endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
async def get_progress(user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Return per-topic mastery levels for the authenticated user."""
    user_id = user.get("id", "anonymous")

    try:
        from src.data.supabase import get_supabase_client

        client = get_supabase_client()
        response = (
            await client.table("user_topics")
            .select("topic_id, mastery_level, last_practiced_at")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data or []
    except Exception:
        # Return empty list when DB is not configured (local dev mode)
        return []
