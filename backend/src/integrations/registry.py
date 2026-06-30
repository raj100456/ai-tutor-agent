"""
Integration Registry — plugin bus for all external integrations.

Integrations are registered at import time via @IntegrationRegistry.register().
At startup, only integrations listed in config.yaml → integrations.enabled
are instantiated and initialised.

Usage:
    # Get a ready integration by name
    discord = await IntegrationRegistry.get("discord")
    await discord.send(...)

    # List all registered/enabled
    IntegrationRegistry.list_registered()
    await IntegrationRegistry.list_enabled()
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from src.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)

_RegistryEntry = type[BaseIntegration]


class IntegrationRegistry:
    _registry: dict[str, _RegistryEntry] = {}
    _instances: dict[str, BaseIntegration] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    @classmethod
    def register(cls, name: str) -> Callable[[_RegistryEntry], _RegistryEntry]:
        """Decorator: register an integration class under a config key name."""
        def wrapper(integration_class: _RegistryEntry) -> _RegistryEntry:
            cls._registry[name] = integration_class
            logger.debug("Registered integration: %s", name)
            return integration_class
        return wrapper

    # ── Retrieval ─────────────────────────────────────────────────────────────

    @classmethod
    async def get(cls, name: str) -> BaseIntegration:
        """
        Return an initialised integration instance by name.
        Lazily initialises on first access.
        """
        if name not in cls._instances:
            await cls._load(name)
        instance = cls._instances[name]
        if not instance.is_ready:
            raise RuntimeError(
                f"Integration '{name}' exists but failed to initialise. "
                "Check logs for details."
            )
        return instance

    @classmethod
    async def get_or_none(cls, name: str) -> BaseIntegration | None:
        """Return integration if available and ready; None otherwise."""
        try:
            return await cls.get(name)
        except Exception as exc:
            logger.warning("Integration '%s' not available: %s", name, exc)
            return None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @classmethod
    async def load_enabled(cls) -> None:
        """
        Initialise all integrations listed in config.yaml → integrations.enabled.
        Called once at application startup.
        """
        from src.config.settings import get_settings

        enabled = get_settings().get_enabled_integrations()
        for name in enabled:
            try:
                await cls._load(name)
                logger.info("Integration '%s' loaded successfully", name)
            except Exception as exc:
                logger.error("Failed to load integration '%s': %s", name, exc)

    @classmethod
    async def shutdown_all(cls) -> None:
        """Gracefully shut down all initialised integrations."""
        for name, instance in list(cls._instances.items()):
            try:
                await instance.shutdown()
                logger.info("Integration '%s' shut down", name)
            except Exception as exc:
                logger.warning("Error shutting down '%s': %s", name, exc)
        cls._instances.clear()

    @classmethod
    async def _load(cls, name: str) -> None:
        from src.config.settings import get_settings

        if name not in cls._registry:
            raise KeyError(
                f"Integration '{name}' is not registered.\n"
                f"Registered integrations: {list(cls._registry.keys())}\n"
                f"Implement BaseIntegration and decorate with "
                f"@IntegrationRegistry.register('{name}')."
            )
        cfg = get_settings().get_integration_config(name)
        instance = cls._registry[name](cfg)
        await instance.initialize()
        cls._instances[name] = instance

    # ── Introspection ─────────────────────────────────────────────────────────

    @classmethod
    def list_registered(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def list_active(cls) -> list[dict[str, Any]]:
        return [
            {"name": name, "ready": inst.is_ready}
            for name, inst in cls._instances.items()
        ]


# ── Auto-load built-in integrations ──────────────────────────────────────────
# Import side-effectfully so @register calls execute, making them discoverable.
from src.integrations import notifier  # noqa: E402, F401
from src.integrations import mcp       # noqa: E402, F401
