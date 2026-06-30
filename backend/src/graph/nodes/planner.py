"""
Planner node — generates and updates adaptive learning plans.

Produces a structured milestone-based plan for the user's selected topic
using config.yaml → tutor.topics as the curriculum reference.
Persists the plan to Supabase and populates state['plan'].
"""
from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.config.settings import get_settings
from src.graph.state import TutorState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

_PLANNER_SYSTEM = """You are a technical interview preparation expert.
Create a structured learning plan for the given topic.
The student is a senior software engineer targeting FAANG / staff-level roles.

Output valid JSON with this schema:
{{
  "topic": "<topic_id>",
  "title": "<human readable title>",
  "estimated_hours": <number>,
  "milestones": [
    {{
      "id": "<milestone_id>",
      "title": "<title>",
      "subtopics": ["<subtopic1>", ...],
      "practice_items": [
        {{"type": "mcq|coding|system_design|behavioral", "description": "<description>"}}
      ],
      "estimated_minutes": <number>,
      "prerequisite_ids": ["<milestone_id>", ...]
    }}
  ]
}}
Return ONLY the JSON. No markdown, no explanation."""


async def planner_node(state: TutorState, config: RunnableConfig) -> dict[str, Any]:
    """Generate or update the learning plan for the current topic."""
    settings = get_settings()
    topic = state.get("topic") or "system_design"
    user_id = state.get("user_id", "anonymous")

    # Find topic config
    topics = settings.tutor.get("topics", [])
    topic_cfg = next((t for t in topics if t["id"] == topic), None)
    topic_name = topic_cfg["name"] if topic_cfg else topic.replace("_", " ").title()

    llm = get_llm("planning")

    prompt = (
        f"Create a comprehensive learning plan for: {topic_name}\n"
        f"Subtopics to cover: {json.dumps(topic_cfg.get('subtopics', []) if topic_cfg else [])}\n"
        f"Target: FAANG/staff-level interview readiness"
    )

    plan_data: dict[str, Any] = {}
    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=_PLANNER_SYSTEM),
                HumanMessage(content=prompt),
            ],
            config=config,
        )
        raw = str(response.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        plan_data = json.loads(raw)
    except Exception as exc:
        logger.error("Plan generation failed: %s", exc)
        plan_data = {
            "topic": topic,
            "title": f"{topic_name} Study Plan",
            "estimated_hours": 20,
            "milestones": [],
            "error": str(exc),
        }

    # Persist to Supabase (non-blocking; failures are logged, not raised)
    try:
        from src.data.supabase import get_supabase_client

        client = get_supabase_client()
        await client.table("plans").upsert(
            {
                "user_id": user_id,
                "topic_id": topic,
                "milestones": plan_data.get("milestones", []),
                "status": "active",
            }
        ).execute()
    except Exception as exc:
        logger.warning("Could not persist plan to Supabase: %s", exc)

    return {"plan": plan_data}
