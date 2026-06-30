"""
Conditional edge routing — maps state['intent'] to the next graph node.
"""
from __future__ import annotations

from typing import Literal

from src.graph.state import TutorState

NodeName = Literal["planner", "evaluator", "knowledge_feed", "chat"]


def route_from_intent(state: TutorState) -> NodeName:
    """
    Route after intent_classifier based on the classified intent.
    Falls back to 'chat' for any unrecognised or missing intent.
    """
    intent = (state.get("intent") or "chat").lower()
    routing: dict[str, NodeName] = {
        "plan":     "planner",
        "practice": "evaluator",
        "feed":     "knowledge_feed",
        "chat":     "chat",
    }
    return routing.get(intent, "chat")
