"""
Supabase async client — singleton with lazy initialisation.

Config comes from config.yaml → data (with env refs resolved):
  supabase_url, supabase_anon_key, supabase_service_key

Usage:
    from src.data.supabase import get_supabase_client
    client = get_supabase_client()
    await client.table("plans").select("*").execute()
"""
from __future__ import annotations

import logging
from functools import lru_cache

from supabase import AsyncClient, create_async_client

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: AsyncClient | None = None


async def init_supabase() -> None:
    """Call once at application startup."""
    global _client
    settings = get_settings()
    data_cfg = settings.data

    url = data_cfg.get("supabase_url", "")
    key = data_cfg.get("supabase_service_key", "") or data_cfg.get("supabase_anon_key", "")

    if not url or not key:
        logger.warning(
            "Supabase URL or key not configured. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env. "
            "Running without persistence."
        )
        return

    _client = await create_async_client(url, key)
    logger.info("Supabase client initialised: %s", url)


def get_supabase_client() -> AsyncClient:
    if _client is None:
        raise RuntimeError(
            "Supabase client not initialised. "
            "Call await init_supabase() at startup, or configure "
            "SUPABASE_URL and SUPABASE_SERVICE_KEY in .env."
        )
    return _client
