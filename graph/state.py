"""
graph/state.py — LangGraph shared state definition.

Defines the TypedDict that flows through every node in the
Storyverse workflow graph.
"""

from __future__ import annotations

from typing import TypedDict


class StoryverseState(TypedDict):
    """Shared state carried across every LangGraph node."""

    # The authenticated / session user identifier.
    user_id: str

    # The raw text the user provided in this turn.
    user_input: str

    # 0-100 integer reflecting how complete the world bible is.
    # 80+ means the world is ready for story drafting.
    clarity_score: int

    # Structured world-building context extracted from the interview
    # (setting, characters, tone, themes, etc.).
    world_bible: dict

    # Elements the Architect flagged as still missing.
    missing_elements: list[str]

    # Rolling history of interview Q&A turns.
    interview_history: list[dict[str, str]]

    # The Inquisitor's latest follow-up question (empty if interview is done).
    follow_up_question: str

    # The generated prose / narrative draft.
    story_draft: str

    # File paths (or URLs) for any images produced by downstream
    # nodes (comic panels, meme assets, etc.).
    image_paths: list[str]
