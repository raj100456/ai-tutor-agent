"""
TutorState — the shared state object passed through every LangGraph node.

All nodes receive the full state and return a *partial* update dict.
LangGraph merges partial updates into the running state automatically.
The ``messages`` field uses the built-in ``add_messages`` reducer so
new messages are appended rather than replaced.
"""
from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class TutorState(TypedDict):
    # ── Identity ─────────────────────────────────────────────────────────────
    user_id: str
    session_id: str

    # ── Conversation (append-only via add_messages reducer) ──────────────────
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Current context ───────────────────────────────────────────────────────
    topic: str | None            # e.g. "system_design"
    subtopic: str | None         # e.g. "caching_strategies"
    plan: dict[str, Any] | None  # Active learning plan milestone data

    # ── Routing ───────────────────────────────────────────────────────────────
    # Set by intent_classifier; consumed by conditional edges
    intent: str | None           # "chat" | "plan" | "practice" | "feed"

    # ── Evaluation ────────────────────────────────────────────────────────────
    evaluation_result: dict[str, Any] | None
    mastery_level: float | None  # 0.0–1.0 for current topic

    # ── Behaviour modifiers ───────────────────────────────────────────────────
    # Decorator names applied at runtime; loaded from config or user settings
    active_decorators: list[str]

    # ── Knowledge feed ────────────────────────────────────────────────────────
    knowledge_items: list[dict[str, Any]] | None

    # ── Feedback loop ─────────────────────────────────────────────────────────
    last_feedback: dict[str, Any] | None

    # ── Internal metadata ─────────────────────────────────────────────────────
    iteration_count: int
    error: str | None
