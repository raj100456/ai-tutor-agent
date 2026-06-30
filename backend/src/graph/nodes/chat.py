"""
Chat node — the final response node for all conversation turns.

Applies the active decorator stack to the LLM before invoking.
Receives enriched state from planner/evaluator/knowledge_feed and
assembles the final streaming-friendly response.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.config.settings import get_settings
from src.graph.decorators.registry import DecoratorRegistry
from src.graph.state import TutorState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)


def _build_system_prompt(state: TutorState, settings_data: dict[str, Any]) -> str:
    """Compose the system prompt from config + current state context."""
    base_prompt = settings_data.get("system_prompt", "You are a helpful tutor.")

    context_parts = [base_prompt]

    if topic := state.get("topic"):
        context_parts.append(f"\nCurrent topic: {topic.replace('_', ' ').title()}")

    if subtopic := state.get("subtopic"):
        context_parts.append(f"Current subtopic: {subtopic.replace('_', ' ').title()}")

    if mastery := state.get("mastery_level"):
        context_parts.append(
            f"Student mastery on this topic: {mastery * 100:.0f}/100"
        )

    if plan := state.get("plan"):
        milestone_titles = [m.get("title", "") for m in plan.get("milestones", [])[:3]]
        context_parts.append(f"Active learning plan milestones: {', '.join(milestone_titles)}")

    if eval_result := state.get("evaluation_result"):
        gaps = eval_result.get("gaps", [])
        if gaps:
            context_parts.append(f"Known knowledge gaps to address: {'; '.join(gaps[:3])}")

    if feed_items := state.get("knowledge_items"):
        if feed_items and feed_items[0].get("summary"):
            context_parts.append(
                f"\nRecent relevant content:\n{feed_items[0]['summary']}"
            )

    return "\n".join(context_parts)


async def chat_node(state: TutorState, config: RunnableConfig) -> dict[str, Any]:
    """Assemble and invoke the final LLM response with decorator stack applied."""
    settings = get_settings()
    active_decorators = state.get("active_decorators", [])

    # Build base LLM
    llm = get_llm("chat")

    # Apply decorator stack (order matters — first applied = outermost)
    for decorator_name in active_decorators:
        try:
            decorator = DecoratorRegistry.get(decorator_name)
            decorator_cfg = settings.get_decorator_config(decorator_name)
            llm = decorator(llm, decorator_cfg)
        except KeyError:
            logger.warning("Decorator '%s' not registered; skipping", decorator_name)

    system_prompt = _build_system_prompt(state, settings.tutor)
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    messages.extend(state.get("messages", []))

    try:
        response = await llm.ainvoke(messages, config=config)
    except Exception as exc:
        logger.error("Chat node LLM call failed: %s", exc)
        response = AIMessage(content=f"I encountered an error: {exc}. Please try again.")

    return {"messages": [response], "error": None}
