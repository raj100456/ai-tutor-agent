"""
Abstract base for all integrations (notifiers, MCP, calendar, etc.).

HOW TO ADD A NEW INTEGRATION:
  1. Create src/integrations/my_integration.py extending BaseIntegration.
  2. Decorate the class with @IntegrationRegistry.register("my_integration").
  3. Add its config block to config.yaml → integrations.
  4. Add its name to config.yaml → integrations.enabled.
  ─ No further code changes required. ─
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseIntegration(ABC):
    """
    Every integration plugin must implement this interface.
    Lifecycle: initialize() → use → shutdown()
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._ready = False

    @abstractmethod
    async def initialize(self) -> None:
        """Connect, authenticate, validate — called once at startup."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up connections and resources."""
        ...

    @property
    def is_ready(self) -> bool:
        return self._ready

    def _mark_ready(self) -> None:
        self._ready = True

    def _require(self, *keys: str) -> None:
        for key in keys:
            if not self.config.get(key):
                raise ValueError(
                    f"{self.__class__.__name__} requires '{key}' in "
                    f"config.yaml → integrations"
                )
