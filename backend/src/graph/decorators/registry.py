"""
Decorator Registry — runtime behaviour modifiers for the LLM.

Decorators are higher-order functions that wrap a BaseChatModel
and alter its behaviour (system prompt injection, parameter overrides,
response post-processing) without modifying underlying provider code.

HOW TO ADD A DECORATOR:
  1. Create src/graph/decorators/my_decorator.py implementing the signature:
         def my_decorator(llm: BaseChatModel, cfg: dict) -> BaseChatModel
  2. Register it below with @DecoratorRegistry.register("my_decorator").
  3. Add its config block to config.yaml → decorators.available.
  4. Enable it via config.yaml → tutor.active_decorators or via API.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)

DecoratorFn = Callable[[BaseChatModel, dict[str, Any]], BaseChatModel]


class DecoratorRegistry:
    _registry: dict[str, DecoratorFn] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[DecoratorFn], DecoratorFn]:
        """Class decorator to register a behaviour modifier by name."""
        def wrapper(fn: DecoratorFn) -> DecoratorFn:
            cls._registry[name] = fn
            logger.debug("Registered LLM decorator: %s", name)
            return fn
        return wrapper

    @classmethod
    def get(cls, name: str) -> DecoratorFn:
        """Return the decorator function for the given name."""
        fn = cls._registry.get(name)
        if fn is None:
            available = list(cls._registry.keys())
            raise KeyError(
                f"Decorator '{name}' not registered.\n"
                f"Registered decorators: {available}\n"
                f"Register it with @DecoratorRegistry.register('{name}')."
            )
        return fn

    @classmethod
    def list_registered(cls) -> list[str]:
        return list(cls._registry.keys())


# ── Auto-load built-in decorators ────────────────────────────────────────────
# Import side-effectfully so @register calls execute at startup.
from src.graph.decorators import exam_mode, socratic_mode, strict_pacing  # noqa: E402, F401
