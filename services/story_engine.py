"""
services/story_engine.py — The Infinite Weaver intelligence engine.

Houses all LLM-powered logic for the Storyverse pipeline:
  • Architect  — evaluates user input and builds the world bible
  • Inquisitor — generates immersive follow-up questions
  • Scribe     — drafts narrative chapters from the world bible

All models are served through OpenRouter.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from core.config import OPENROUTER_API_KEY

# ---------------------------------------------------------------------------
# OpenRouter-backed LLM clients
# ---------------------------------------------------------------------------

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Architect & Inquisitor — fast, cheap, great at structured output
architect_llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=OPENROUTER_API_KEY,
    base_url=_OPENROUTER_BASE,
    temperature=0.4,
    max_tokens=2048,
)

inquisitor_llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=OPENROUTER_API_KEY,
    base_url=_OPENROUTER_BASE,
    temperature=0.7,
    max_tokens=2048,
)

# Scribe — higher-quality model for long-form prose
scribe_llm = ChatOpenAI(
    model="google/gemini-2.5-pro",
    api_key=OPENROUTER_API_KEY,
    base_url=_OPENROUTER_BASE,
    temperature=0.8,
    max_tokens=2048,
)


# ---------------------------------------------------------------------------
# Structured output schema for the Architect
# ---------------------------------------------------------------------------


class WorldBibleEvaluation(BaseModel):
    """Schema the Architect must return when evaluating the world bible."""

    clarity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "0-100 integer indicating how complete and self-consistent "
            "the world bible is.  100 = fully fleshed-out and ready to write."
        ),
    )
    world_bible: dict = Field(
        ...,
        description=(
            "The updated world bible dictionary. Must contain all known "
            "details: setting, time_period, characters (with names, roles, "
            "motivations), tone, themes, conflict, and any other relevant "
            "world-building elements gathered so far."
        ),
    )
    missing_elements: list[str] = Field(
        ...,
        description=(
            "A list of world-building elements still missing or under-specified. "
            "Examples: 'protagonist motivation', 'magic system rules', "
            "'antagonist backstory'.  Empty list when clarity_score >= 80."
        ),
    )


# ---------------------------------------------------------------------------
# Architect — evaluate the world bible
# ---------------------------------------------------------------------------

_ARCHITECT_SYSTEM = """\
You are **The Architect**, a master world-builder for the Storyverse engine.

Your job is to evaluate the user's latest input against the current world bible
and interview history, then return an updated assessment.

Rules:
1. Merge new information from the user's input into the existing world_bible.
2. Never discard previously established facts unless the user explicitly
   contradicts them.
3. Score `clarity_score` from 0-100 based on how complete and internally
   consistent the world bible is.  A score of 80+ means the world is ready
   for a story draft.
4. List every under-specified element in `missing_elements`.  Be specific
   (e.g. "protagonist's core motivation" not just "character details").
5. Return ONLY the requested JSON structure — no commentary.
"""


def evaluate_world_bible(
    user_input: str,
    world_bible: dict,
    interview_history: list[dict[str, str]],
) -> dict:
    """Ask the Architect to evaluate and update the world bible.

    Returns a validated dictionary `{"clarity_score": int, "world_bible": dict, "missing_elements": list}`.
    """
    history_text = "\n".join(
        f"Q: {turn.get('question', '')}\nA: {turn.get('answer', '')}"
        for turn in interview_history
    ) or "(no prior interview history)"

    human_prompt = (
        f"## Current World Bible\n```json\n{json.dumps(world_bible, indent=2)}\n```\n\n"
        f"## Interview History\n{history_text}\n\n"
        f"## Latest User Input\n{user_input}\n\n"
        "Evaluate the world bible now."
    )

    structured_llm = architect_llm.with_structured_output(WorldBibleEvaluation)

    raw_result = structured_llm.invoke([
        SystemMessage(content=_ARCHITECT_SYSTEM),
        HumanMessage(content=human_prompt),
    ])

    # Defensive: with_structured_output may return a raw dict depending
    # on the provider.
    if hasattr(raw_result, "model_dump"):
        return raw_result.model_dump()
    elif hasattr(raw_result, "dict"):
        return raw_result.dict()
    elif isinstance(raw_result, dict):
        return raw_result

    # raw_result is unexpected type — return empty-ish fallback
    return {
        "clarity_score": 0,
        "world_bible": {},
        "missing_elements": [],
    }


# ---------------------------------------------------------------------------
# Inquisitor — generate follow-up questions
# ---------------------------------------------------------------------------

_INQUISITOR_SYSTEM = """\
You are **The Inquisitor**, a deeply immersive interviewer for the Storyverse
engine.  Your goal is to coax rich world-building details from the user
through a single, captivating question.

Rules:
1. You receive the current world bible, a list of missing elements, and the
   interview history so far.
2. Pick the MOST IMPORTANT missing element and craft ONE evocative question
   that naturally draws out the answer.
3. Write the question in-character — as if you are a curious bard or scholar
   who lives inside the story world.  Make it vivid and immersive.
4. NEVER ask a yes/no question.  Always invite creative elaboration.
5. Return ONLY the question text — no preamble, no explanation.
"""


def generate_follow_up_question(
    world_bible: dict,
    missing_elements: list[str],
    interview_history: list[dict[str, str]],
) -> str:
    """Ask the Inquisitor to produce a single immersive follow-up question."""
    history_text = "\n".join(
        f"Q: {turn.get('question', '')}\nA: {turn.get('answer', '')}"
        for turn in interview_history
    ) or "(first question — no history yet)"

    human_prompt = (
        f"## World Bible So Far\n```json\n{json.dumps(world_bible, indent=2)}\n```\n\n"
        f"## Missing Elements\n- " + "\n- ".join(missing_elements) + "\n\n"
        f"## Interview History\n{history_text}\n\n"
        "Generate your single follow-up question now."
    )

    response = inquisitor_llm.invoke([
        SystemMessage(content=_INQUISITOR_SYSTEM),
        HumanMessage(content=human_prompt),
    ])

    return response.content.strip()


# ---------------------------------------------------------------------------
# Scribe — draft a chapter
# ---------------------------------------------------------------------------

_SCRIBE_SYSTEM_TEMPLATE = """\
You are **The Scribe**, the master storyteller of the Storyverse engine.

You will receive a fully-formed world bible as your ONLY source of truth.
Write a compelling opening chapter (1,500-2,500 words) that brings this
world to life.

ABSOLUTE RULES — violation means failure:
1. **Zero hallucination** — use ONLY facts from the world bible below.
   Do not invent characters, locations, magic systems, or events that are
   not established in the bible.
2. **Show, don't tell** — immerse the reader through vivid sensory detail,
   dialogue, and action.
3. **Hook the reader** — open with a scene that immediately creates tension
   or wonder.
4. **End with a cliffhanger** — leave the reader desperate for Chapter 2.

## World Bible (SOURCE OF TRUTH)
```json
{world_bible_json}
```

Write Chapter 1 now.  Output ONLY the chapter text — no meta-commentary.
"""


def draft_chapter(world_bible: dict) -> str:
    """Ask the Scribe to draft Chapter 1 from the world bible."""
    system_content = _SCRIBE_SYSTEM_TEMPLATE.format(
        world_bible_json=json.dumps(world_bible, indent=2)
    )

    response = scribe_llm.invoke([
        SystemMessage(content=system_content),
        HumanMessage(content="Begin writing Chapter 1."),
    ])

    return response.content.strip()
