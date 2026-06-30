"""Abstract base for all LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel


class AbstractLLMProvider(ABC):
    """
    Every LLM provider must implement this interface.

    To add a new provider:
      1. Create ``src/llm/providers/my_provider.py`` extending this class.
      2. Register it in ``src/llm/factory.py`` PROVIDER_REGISTRY.
      3. Add its config block to ``config.yaml → llm.providers``.
      No other changes needed.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """Raise ValueError if required config keys are missing."""
        ...

    @abstractmethod
    def build(self) -> BaseChatModel:
        """Instantiate and return a LangChain BaseChatModel."""
        ...

    def _require(self, *keys: str) -> None:
        """Helper: raise if any required key is absent or empty."""
        for key in keys:
            if not self.config.get(key):
                raise ValueError(
                    f"{self.__class__.__name__} requires '{key}' in "
                    f"config.yaml → llm.providers.{self.config.get('type', '?')}"
                )
