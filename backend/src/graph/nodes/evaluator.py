"""
Evaluator node — scores user answers and updates mastery levels.

Handles: MCQ, open-ended explanations, coding solutions, system design reviews.
Updates user_topics.mastery_level in Supabase.
Populates state['evaluation_result'].
"""
from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import TutorState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

_EVALUATOR_SYSTEM = """You are a rigorous technical interview evaluator.
Assess the student's answer against the question/topic provided.
The student is targeting FAANG/staff-level roles — hold a high bar.

Respond with valid JSON:
{{
  "score": <0-100>,
  "mastery_delta": <-0.1 to 0.2>,
  "passed": <true|false>,
  "strengths": ["<point>", ...],
  "gaps": ["<gap>", ...],
  "follow_up_question": "<targeted follow-up or empty string>",
  "detailed_feedback": "<concise, direct feedback paragraph>"
}}
Return ONLY the JSON."""


async def evaluator_node(state: TutorState, config: RunnableConfig) -> dict[str, Any]:
    """Score the latest user answer and update mastery tracking."""
    messages = state.get("messages", [])
    topic = state.get("topic", "general")
    current_mastery = state.get("mastery_level") or 0.5
    user_id = state.get("user_id", "anonymous")

    # Build evaluation context from the last few turns
    eval_context = "\n".join(
        f"{m.__class__.__name__}: {m.content}" for m in messages[-6:]
    )

    llm = get_llm("evaluation")

    result: dict[str, Any] = {}
    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=_EVALUATOR_SYSTEM),
                HumanMessage(
                    content=(
                        f"Topic: {topic}\n"
                        f"Current mastery level: {current_mastery:.2f}\n"
                        f"Conversation context:\n{eval_context}"
                    )
                ),
            ],
            config=config,
        )
        raw = str(response.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        result = json.loads(raw)
    except Exception as exc:
        logger.error("Evaluation failed: %s", exc)
        result = {
            "score": 50,
            "mastery_delta": 0.0,
            "passed": False,
            "strengths": [],
            "gaps": ["Evaluation error — please try again"],
            "follow_up_question": "",
            "detailed_feedback": f"Evaluation failed: {exc}",
        }

    # Update mastery level (clamped to [0.0, 1.0])
    delta = float(result.get("mastery_delta", 0.0))
    new_mastery = max(0.0, min(1.0, current_mastery + delta))

    # Persist mastery to Supabase
    try:
        from src.data.supabase import get_supabase_client

        client = get_supabase_client()
        await client.table("user_topics").upsert(
            {
                "user_id": user_id,
                "topic_id": topic,
                "mastery_level": int(new_mastery * 100),
            }
        ).execute()
    except Exception as exc:
        logger.warning("Could not persist mastery to Supabase: %s", exc)

    return {
        "evaluation_result": result,
        "mastery_level": new_mastery,
    }
