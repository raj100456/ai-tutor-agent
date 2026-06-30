"""
Tutor API — the primary chat endpoint with SSE streaming.

POST /api/tutor/chat     — single-turn (returns full response)
POST /api/tutor/stream   — streaming via Server-Sent Events

Both endpoints invoke the LangGraph StateGraph and persist the
thread via the configured checkpointer (memory or postgres).
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.api.deps import get_current_user
from src.graph.graph import build_graph
from src.graph.state import TutorState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tutor", tags=["tutor"])


# ── Request / Response schemas ────────────────────────────────────────────────

class TutorRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str | None = Field(default=None)
    subtopic: str | None = Field(default=None)
    active_decorators: list[str] = Field(default_factory=list)


class TutorResponse(BaseModel):
    session_id: str
    message: str
    intent: str | None
    evaluation_result: dict[str, Any] | None
    mastery_level: float | None
    knowledge_items: list[dict[str, Any]] | None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_initial_state(req: TutorRequest, user_id: str) -> TutorState:
    return TutorState(
        user_id=user_id,
        session_id=req.session_id,
        messages=[HumanMessage(content=req.message)],
        topic=req.topic,
        subtopic=req.subtopic,
        plan=None,
        intent=None,
        evaluation_result=None,
        mastery_level=None,
        active_decorators=req.active_decorators,
        knowledge_items=None,
        last_feedback=None,
        iteration_count=0,
        error=None,
    )


async def _stream_graph(
    req: TutorRequest, user_id: str
) -> AsyncGenerator[str, None]:
    """Stream LangGraph events as SSE data frames."""
    graph = build_graph()
    state = _build_initial_state(req, user_id)
    thread_config = {"configurable": {"thread_id": req.session_id}}

    try:
        async for event in graph.astream_events(
            state, config=thread_config, version="v2"
        ):
            event_type = event.get("event", "")

            # Stream AI message chunks as they arrive
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield json.dumps(
                        {"type": "chunk", "content": str(chunk.content)}
                    )

            # Emit node completion events for UI progress indicators
            elif event_type == "on_chain_end":
                node_name = event.get("name", "")
                if node_name in ("planner", "evaluator", "knowledge_feed"):
                    output = event.get("data", {}).get("output", {})
                    yield json.dumps({"type": "node_complete", "node": node_name, "data": output})

        yield json.dumps({"type": "done"})

    except Exception as exc:
        logger.error("Graph stream error: %s", exc)
        yield json.dumps({"type": "error", "message": str(exc)})


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/stream")
async def stream_chat(
    req: TutorRequest,
    user: dict = Depends(get_current_user),
) -> EventSourceResponse:
    """
    Stream a tutor response via Server-Sent Events.

    Angular client example:
        const source = new EventSource('/api/tutor/stream');
        // or use fetch() + ReadableStream for auth headers (recommended)
    """
    user_id = user.get("id", "anonymous")

    async def _event_generator() -> AsyncGenerator[dict, None]:
        async for data in _stream_graph(req, user_id):
            yield {"data": data}

    return EventSourceResponse(_event_generator())


@router.post("/chat", response_model=TutorResponse)
async def chat(
    req: TutorRequest,
    user: dict = Depends(get_current_user),
) -> TutorResponse:
    """Non-streaming single-turn chat. Returns full response when complete."""
    user_id = user.get("id", "anonymous")
    graph = build_graph()
    state = _build_initial_state(req, user_id)
    thread_config = {"configurable": {"thread_id": req.session_id}}

    try:
        final_state = await graph.ainvoke(state, config=thread_config)
    except Exception as exc:
        logger.error("Graph invocation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    messages = final_state.get("messages", [])
    last_ai_msg = next(
        (m for m in reversed(messages) if hasattr(m, "content") and not isinstance(m, HumanMessage)),
        None,
    )

    return TutorResponse(
        session_id=req.session_id,
        message=str(last_ai_msg.content) if last_ai_msg else "",
        intent=final_state.get("intent"),
        evaluation_result=final_state.get("evaluation_result"),
        mastery_level=final_state.get("mastery_level"),
        knowledge_items=final_state.get("knowledge_items"),
    )
