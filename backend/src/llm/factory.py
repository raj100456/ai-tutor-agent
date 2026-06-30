"""
LLM Provider Registry and Factory.

HOW TO ADD A NEW PROVIDER:
  1. Create src/llm/providers/my_provider.py implementing AbstractLLMProvider.
  2. Import and register it in PROVIDER_REGISTRY below.
  3. Add its config block to config.yaml → llm.providers.
  4. Set it in config.yaml → llm.task_providers.<task>.
  ─ That's it. No further code changes required. ─

Usage:
    from src.llm.factory import get_llm
    llm = get_llm("chat")         # returns BaseChatModel per config
    llm = get_llm("planning")
"""
from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel

from src.config.settings import get_settings
from src.llm.circuit_breaker import with_fallback_chain
from src.llm.providers.anthropic_provider import AnthropicProvider
from src.llm.providers.azure_openai_provider import AzureOpenAIProvider
from src.llm.providers.base import AbstractLLMProvider
from src.llm.providers.google_provider import GoogleProvider
from src.llm.providers.llamacpp import LlamaCppProvider
from src.llm.providers.ollama_provider import OllamaProvider
from src.llm.providers.openai_provider import OpenAIProvider

TaskType = Literal["chat", "planning", "evaluation", "classification", "knowledge_feed"]

# ── Provider registry ─────────────────────────────────────────────────────────
# Map config.yaml type strings to provider classes.
# Extend this dict to register new providers.
PROVIDER_REGISTRY: dict[str, type[AbstractLLMProvider]] = {
    "llamacpp":    LlamaCppProvider,
    "openai":      OpenAIProvider,
    "anthropic":   AnthropicProvider,
    "google":      GoogleProvider,
    "ollama":      OllamaProvider,
    "azure_openai": AzureOpenAIProvider,
}


def _build_llm(provider_name: str) -> BaseChatModel:
    """Instantiate a BaseChatModel for the given provider name."""
    settings = get_settings()
    cfg = settings.get_provider_config(provider_name)

    provider_type = cfg.get("type", provider_name)
    provider_class = PROVIDER_REGISTRY.get(provider_type)

    if provider_class is None:
        available = list(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown LLM provider type '{provider_type}'.\n"
            f"Registered providers: {available}\n"
            f"Add a new provider class to PROVIDER_REGISTRY in src/llm/factory.py."
        )

    return provider_class(cfg).build()


def get_llm(task: TaskType = "chat") -> BaseChatModel:
    """
    Return a BaseChatModel for the given task type.

    Provider is resolved from:
        config.yaml → llm.task_providers[task]

    If the primary provider fails, the fallback chain from
        config.yaml → llm.fallback_chain
    is tried in order, wrapped in tenacity retry logic.

    Switching providers: change config.yaml only — no code changes.
    """
    settings = get_settings()
    primary = settings.get_task_provider(task)
    fallback_chain = settings.get_fallback_chain()
    cb_cfg = settings.get_circuit_breaker_cfg()

    # Build primary + fallback models lazily
    def _primary() -> BaseChatModel:
        return _build_llm(primary)

    def _fallbacks() -> list[BaseChatModel]:
        return [_build_llm(name) for name in fallback_chain if name != primary]

    return with_fallback_chain(_primary, _fallbacks, cb_cfg)
