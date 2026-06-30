"""Socratic mode — guide through questions, not answers."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda

from src.graph.decorators.registry import DecoratorRegistry


@DecoratorRegistry.register("socratic_mode")
def socratic_mode(llm: BaseChatModel, cfg: dict[str, Any]) -> BaseChatModel:
    """Force the LLM to guide via questions rather than direct answers."""
    q_ratio = cfg.get("question_ratio", 0.8)
    max_direct = cfg.get("max_direct_answers_per_session", 2)

    extra = (
        "\n\n[SOCRATIC MODE ACTIVE]\n"
        f"• {int(q_ratio * 100)}% of your responses must be guiding questions.\n"
        "• Do NOT give direct answers unless the student is completely stuck.\n"
        "• Ask one question at a time — targeted and specific.\n"
        "• Build on the student's reasoning; correct misconceptions with questions.\n"
        f"• You may give at most {max_direct} direct answers this session.\n"
    )

    async def _inject(messages: list, **kwargs: Any) -> Any:
        augmented = list(messages)
        for i, msg in enumerate(augmented):
            if isinstance(msg, SystemMessage):
                augmented[i] = SystemMessage(content=msg.content + extra)
                break
        else:
            augmented.insert(0, SystemMessage(content=extra))
        return await llm.ainvoke(augmented, **kwargs)

    return RunnableLambda(_inject)  # type: ignore[return-value]
