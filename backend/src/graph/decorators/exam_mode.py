"""Exam mode decorator — strict interview simulation."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda

from src.graph.decorators.registry import DecoratorRegistry


@DecoratorRegistry.register("exam_mode")
def exam_mode(llm: BaseChatModel, cfg: dict[str, Any]) -> BaseChatModel:
    """
    Wraps the LLM to simulate a real interview environment.

    Behaviour changes:
      • Prepends a strict no-hints system message.
      • Disables any follow-up hints if hint_allowed=false in config.
      • Forces terse, evaluator-style responses.
    """
    hint_allowed = cfg.get("hint_allowed", False)
    time_limit = cfg.get("time_limit_seconds", 1800)

    extra_instructions = (
        "\n\n[EXAM MODE ACTIVE]\n"
        f"• This is a timed interview simulation ({time_limit // 60} minutes).\n"
        "• Do NOT provide hints, partial solutions, or leading questions.\n"
        "• Evaluate answers strictly. Acknowledge correct parts; highlight gaps.\n"
        "• Ask one focused follow-up question after each answer.\n"
    )
    if not hint_allowed:
        extra_instructions += "• If the student asks for a hint, decline and redirect to problem-solving.\n"

    async def _inject_exam_prompt(messages: list, **kwargs: Any) -> Any:
        # Find and augment the SystemMessage
        augmented = list(messages)
        for i, msg in enumerate(augmented):
            if isinstance(msg, SystemMessage):
                augmented[i] = SystemMessage(content=msg.content + extra_instructions)
                break
        else:
            augmented.insert(0, SystemMessage(content=extra_instructions))
        return await llm.ainvoke(augmented, **kwargs)

    return RunnableLambda(_inject_exam_prompt)  # type: ignore[return-value]
