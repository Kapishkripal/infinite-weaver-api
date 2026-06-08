"""
api/generate.py — /api/generate endpoint router.

Accepts a user prompt (and optional interview context), seeds the
LangGraph state, and returns the final state produced by the
Storyverse workflow.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from graph.state import StoryverseState
from graph.workflow import storyverse_graph

router = APIRouter(prefix="/api", tags=["generate"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    """Payload accepted by POST /api/generate."""

    prompt: str = Field(
        ...,
        min_length=1,
        description="The user's creative prompt or interview answer.",
    )
    user_id: str = Field(
        default="anonymous",
        description="Optional user identifier for session tracking.",
    )
    # Allow the client to pass back accumulated state for multi-turn
    # interview sessions.
    world_bible: dict = Field(
        default_factory=dict,
        description="Previously accumulated world bible (empty on first call).",
    )
    interview_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Rolling Q&A history from prior interview turns.",
    )


class GenerateResponse(BaseModel):
    """Payload returned after the workflow completes."""

    user_id: str
    clarity_score: int
    world_bible: dict
    story_draft: str
    image_paths: list[str]
    missing_elements: list[str] = Field(default_factory=list)
    follow_up_question: str = Field(
        default="",
        description=(
            "Non-empty if the interview is still in progress. "
            "The client should display this question and POST the "
            "user's answer back with the updated world_bible and "
            "interview_history."
        ),
    )
    interview_history: list[dict[str, str]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Kick off the Storyverse LangGraph workflow.

    On the first call the prompt seeds a new world.  On subsequent
    calls the client passes the accumulated world_bible and
    interview_history to continue the Akinator interview loop.
    """

    # Build the initial state that will flow through the graph.
    initial_state: StoryverseState = {
        "user_id": request.user_id,
        "user_input": request.prompt,
        "clarity_score": 0,
        "world_bible": request.world_bible or {"prompt": request.prompt},
        "missing_elements": [],
        "interview_history": request.interview_history,
        "follow_up_question": "",
        "story_draft": "",
        "image_paths": [],
    }

    # Execute the compiled LangGraph workflow with a thread config for memory.
    config = {"configurable": {"thread_id": request.user_id}}
    result = storyverse_graph.invoke(initial_state, config=config)

    return GenerateResponse(**result)
