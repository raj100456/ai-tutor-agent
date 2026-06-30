"""Strict pacing — enforce prerequisite-based progression."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda

from src.graph.decorators.registry import DecoratorRegistry


@DecoratorRegistry.register("strict_pacing")
def strict_pacing(llm: BaseChatModel, cfg: dict[str, Any]) -> BaseChatModel:
    """Block topic skipping; enforce prerequisite mastery before advancing."""
    min_mastery = cfg.get("min_mastery_to_advance", 0.7)
    enforce = cfg.get("enforce_prerequisites", True)

    extra = (
        "\n\n[STRICT PACING ACTIVE]\n"
        "• Do NOT allow the student to skip topics or jump ahead.\n"
        f"• A student must demonstrate ≥{int(min_mastery * 100)}% mastery before advancing.\n"
        "• If the student tries to skip, acknowledge the request but redirect to the current topic.\n"
        "• Complete each milestone before introducing the next one.\n"
    ) if enforce else ""

    async def _inject(messages: list, **kwargs: Any) -> Any:
        if not extra:
            return await llm.ainvoke(messages, **kwargs)
        augmented = list(messages)
        for i, msg in enumerate(augmented):
            if isinstance(msg, SystemMessage):
                augmented[i] = SystemMessage(content=msg.content + extra)
                break
        else:
            augmented.insert(0, SystemMessage(content=extra))
        return await llm.ainvoke(augmented, **kwargs)

    return RunnableLambda(_inject)  # type: ignore[return-value]
