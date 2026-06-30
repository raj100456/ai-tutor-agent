"""
Circuit breaker + retry logic for LLM calls.

Uses tenacity for exponential-backoff retries and LangChain's
.with_fallbacks() for provider-level failover.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from langchain_core.language_models import BaseChatModel
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def with_fallback_chain(
    primary_factory: Callable[[], BaseChatModel],
    fallback_factories: Callable[[], list[BaseChatModel]],
    cfg: dict[str, Any],
) -> BaseChatModel:
    """
    Build a BaseChatModel that:
      1. Retries the primary provider with exponential backoff.
      2. Falls over to each fallback in order if all retries fail.

    Parameters mirror config.yaml → llm.circuit_breaker.
    """
    max_retries: int = cfg.get("max_retries", 3)
    multiplier: float = cfg.get("wait_multiplier_seconds", 1.0)
    wait_max: float = cfg.get("wait_max_seconds", 10.0)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=multiplier, max=wait_max),
        reraise=cfg.get("reraise", True),
        before_sleep=lambda rs: logger.warning(
            "LLM call failed (attempt %d/%d): %s",
            rs.attempt_number,
            max_retries,
            rs.outcome.exception(),
        ),
    )
    def _build_primary() -> BaseChatModel:
        return primary_factory()

    try:
        primary = _build_primary()
    except (RetryError, Exception) as exc:
        logger.error("Primary LLM provider failed after retries: %s", exc)
        fallbacks = fallback_factories()
        if not fallbacks:
            raise
        # Use the first fallback as primary if the primary build failed entirely
        primary = fallbacks[0]
        fallbacks = fallbacks[1:]

    fallbacks = fallback_factories()
    if fallbacks:
        return primary.with_fallbacks(fallbacks)

    return primary
