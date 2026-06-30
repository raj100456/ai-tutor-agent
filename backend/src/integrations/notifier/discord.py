"""Discord notifier integration."""
from __future__ import annotations

import logging

import httpx

from src.integrations.base import BaseIntegration
from src.integrations.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


@IntegrationRegistry.register("discord")
class DiscordIntegration(BaseIntegration):
    """Send messages to a Discord channel via webhook."""

    async def initialize(self) -> None:
        self._require("webhook_url")
        # Validate the webhook is reachable
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(self.config["webhook_url"])
            if resp.status_code not in (200, 204):
                raise ConnectionError(
                    f"Discord webhook unreachable (status {resp.status_code})"
                )
        self._mark_ready()
        logger.info("Discord integration ready")

    async def shutdown(self) -> None:
        pass  # stateless

    async def send(self, message: str, *, title: str = "", embed: bool = False) -> None:
        """Send a message to the configured Discord webhook."""
        username = self.config.get("username", "AI Tutor")
        avatar_url = self.config.get("avatar_url")

        payload: dict = {"username": username}
        if avatar_url:
            payload["avatar_url"] = avatar_url

        if embed and title:
            payload["embeds"] = [{"title": title, "description": message, "color": 0x5865F2}]
        else:
            payload["content"] = f"**{title}**\n{message}" if title else message

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(self.config["webhook_url"], json=payload)
            resp.raise_for_status()
