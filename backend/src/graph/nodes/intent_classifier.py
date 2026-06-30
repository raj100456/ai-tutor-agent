"""
Intent classifier node — determines which graph branch to activate.

Uses a lightweight LLM call (configured via llm.task_providers.classification)
to classify the user's latest message into one of the supported intents.

Intents:
  chat      — general Q&A, explanation, discussion
  plan      — create or update a learning plan
  practice  — answer a practice question / MCQ
  feed      — fetch latest news / knowledge updates
"""
from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import TutorState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

_INTENT_SYSTEM = """You are an intent classifier for a technical interview tutor.
Classify the user's latest message into exactly one of these intents:
  chat      - general explanation, discussion, or follow-up question
  plan      - requesting a study plan, roadmap, or schedule
  practice  - requesting a practice problem, quiz, or mock interview
  feed      - requesting latest news, trending topics, or recent updates

Respond with a single JSON object:
{"intent": "<intent>", "confidence": <0.0-1.0>}
Do NOT include any other text."""

_VALID_INTENTS = {"chat", "plan", "practice", "feed"}


async def intent_classifier_node(
    state: TutorState, config: RunnableConfig
) -> dict:
    """Classify the latest user message and set state['intent']."""
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "chat", "iteration_count": state.get("iteration_count", 0) + 1}

    # Find last human message
    last_human = next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)), None
    )
    if last_human is None:
        return {"intent": "chat"}

    llm = get_llm("classification")

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=_INTENT_SYSTEM),
                HumanMessage(content=str(last_human.content)),
            ],
            config=config,
        )
        raw = str(response.content).strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()

        parsed = json.loads(raw)
        intent = parsed.get("intent", "chat").lower()
        if intent not in _VALID_INTENTS:
            intent = "chat"
    except Exception as exc:
        logger.warning("Intent classification failed, defaulting to 'chat': %s", exc)
        intent = "chat"

    return {
        "intent": intent,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
