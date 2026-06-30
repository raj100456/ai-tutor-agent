"""
LangGraph StateGraph builder.

The graph topology:
  intent_classifier
       │
  (conditional edges by intent)
       ├─► planner        ─┐
       ├─► evaluator      ─┼─► chat ─► END
       ├─► knowledge_feed ─┘
       └─► chat           ────────────► END

Checkpointer is configured via config.yaml → graph.checkpointer:
  • "memory"   — in-memory (default; works with zero setup)
  • "postgres" — Supabase Postgres (persistent; requires SUPABASE_DATABASE_URL)
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from src.config.settings import get_settings
from src.graph.edges import route_from_intent
from src.graph.nodes.chat import chat_node
from src.graph.nodes.evaluator import evaluator_node
from src.graph.nodes.intent_classifier import intent_classifier_node
from src.graph.nodes.knowledge_feed import knowledge_feed_node
from src.graph.nodes.planner import planner_node
from src.graph.state import TutorState

logger = logging.getLogger(__name__)


def _get_checkpointer(settings_data: dict[str, Any]) -> Any:
    checkpointer_type = settings_data.get("checkpointer", "memory")

    if checkpointer_type == "postgres":
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            db_url = settings_data.get("postgres_url", "")
            if not db_url:
                raise ValueError(
                    "graph.checkpointer is 'postgres' but SUPABASE_DATABASE_URL is not set."
                )
            logger.info("Using PostgreSQL checkpointer for LangGraph")
            return AsyncPostgresSaver.from_conn_string(db_url)
        except ImportError:
            logger.warning(
                "langgraph-checkpoint-postgres not installed; falling back to in-memory."
            )

    logger.info("Using in-memory checkpointer for LangGraph")
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()


@lru_cache(maxsize=1)
def build_graph() -> CompiledGraph:
    """
    Build and compile the TutorState graph.
    Cached — call build_graph() anywhere; same instance is returned.
    """
    settings = get_settings()
    graph_cfg = settings.graph

    g: StateGraph = StateGraph(TutorState)

    # ── Register nodes ───────────────────────────────────────────────────────
    g.add_node("intent_classifier", intent_classifier_node)
    g.add_node("planner",           planner_node)
    g.add_node("evaluator",         evaluator_node)
    g.add_node("knowledge_feed",    knowledge_feed_node)
    g.add_node("chat",              chat_node)

    # ── Entry point ──────────────────────────────────────────────────────────
    g.set_entry_point("intent_classifier")

    # ── Conditional routing after classification ─────────────────────────────
    g.add_conditional_edges(
        "intent_classifier",
        route_from_intent,
        {
            "planner":       "planner",
            "evaluator":     "evaluator",
            "knowledge_feed": "knowledge_feed",
            "chat":          "chat",
        },
    )

    # ── All specialist nodes funnel into chat for final response ─────────────
    g.add_edge("planner",        "chat")
    g.add_edge("evaluator",      "chat")
    g.add_edge("knowledge_feed", "chat")
    g.add_edge("chat",           END)

    checkpointer = _get_checkpointer(settings.data | graph_cfg)
    compiled = g.compile(checkpointer=checkpointer)

    logger.info("LangGraph compiled successfully")
    return compiled
