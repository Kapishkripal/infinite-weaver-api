"""
graph/workflow.py — Storyverse LangGraph workflow.

Implements the 'Infinite Weaver' pipeline:

    START
      → architect_node   (evaluate world bible)
      → [conditional]
          ├─ clarity < 80 → inquisitor_node (ask follow-up) → END
          └─ clarity ≥ 80 → draft_story_node (write chapter + save) →
                             generate_comic (stub) →
                             create_meme (stub) → END
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import StoryverseState
from services.story_engine import (
    evaluate_world_bible,
    generate_follow_up_question,
    draft_chapter,
)
from core.db import supabase


# ---------------------------------------------------------------------------
# Clarity threshold — world bible must score ≥ this to proceed to drafting.
# ---------------------------------------------------------------------------
CLARITY_THRESHOLD = 80


# ---------------------------------------------------------------------------
# Real nodes
# ---------------------------------------------------------------------------


def architect_node(state: StoryverseState) -> dict:
    """Run the Architect to evaluate and update the world bible."""
    print("[node] architect_node - evaluating world bible")

    evaluation = evaluate_world_bible(
        user_input=state.get("user_input", ""),
        world_bible=state.get("world_bible", {}),
        interview_history=state.get("interview_history", []),
    )

    # Force dictionary key access instead of dot notation
    return {
        "clarity_score": evaluation.get("clarity_score", 0),
        "world_bible": evaluation.get("world_bible", {}),
        "missing_elements": evaluation.get("missing_elements", []),
    }


def inquisitor_node(state: StoryverseState) -> dict:
    """Run the Inquisitor to generate an immersive follow-up question."""
    print("[node] inquisitor_node — generating follow-up question")

    question = generate_follow_up_question(
        world_bible=state.get("world_bible", {}),
        missing_elements=state.get("missing_elements", []),
        interview_history=state.get("interview_history", []),
    )

    return {
        "follow_up_question": question,
    }


def draft_story_node(state: StoryverseState) -> dict:
    """Run the Scribe to draft a chapter, then persist to Supabase.

    CRITICAL: Only inserts `user_id`, `title`, and `content` into the
    `stories` table — the `world_bible` dict is NOT inserted.
    """
    print("[node] draft_story_node — drafting chapter")

    chapter_text = draft_chapter(state.get("world_bible", {}))

    # Persist to Supabase — schema-safe insert (no world_bible column).
    try:
        supabase.table("stories").insert({
            "user_id": state.get("user_id", "anonymous"),
            "title": "Chapter 1",
            "content": chapter_text,
        }).execute()
        print("[node] draft_story_node — saved to Supabase")
    except Exception as exc:
        # Log but don't crash the pipeline — the chapter is still returned.
        print(f"[node] draft_story_node — Supabase insert failed: {exc}")

    return {
        "story_draft": chapter_text,
        "follow_up_question": "",  # clear any lingering question
    }


# ---------------------------------------------------------------------------
# Stub nodes (downstream pipeline — implement later)
# ---------------------------------------------------------------------------


def generate_comic(state: StoryverseState) -> dict:
    """Turn the story draft into comic-panel images.

    TODO: Integrate an image-generation service and populate
    `image_paths` with the resulting asset URLs / file paths.
    """
    print("[node] generate_comic — pass-through (stub)")
    return {}


def create_meme(state: StoryverseState) -> dict:
    """Produce shareable meme assets from the story content.

    TODO: Combine story highlights with meme templates and
    append results to `image_paths`.
    """
    print("[node] create_meme — pass-through (stub)")
    return {}


# ---------------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------------


def route_after_evaluation(state: StoryverseState) -> str:
    """Route based on the Architect's clarity score.

    Returns a routing key that maps to a registered node name
    in the conditional edge dictionary.
    """
    score = state.get("clarity_score", 0)
    if score >= CLARITY_THRESHOLD:
        print(f"[router] clarity_score={score} >= {CLARITY_THRESHOLD} -> drafting")
        return "draft_story_node"
    print(f"[router] clarity_score={score} < {CLARITY_THRESHOLD} -> more questions")
    return "inquisitor_node"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_workflow() -> StateGraph:
    """Assemble and compile the Storyverse workflow graph."""
    graph = StateGraph(StoryverseState)

    # ── Register nodes ────────────────────────────────────────────────
    graph.add_node("architect", architect_node)
    graph.add_node("inquisitor", inquisitor_node)
    graph.add_node("draft_story", draft_story_node)
    graph.add_node("generate_comic", generate_comic)
    graph.add_node("create_meme", create_meme)

    # ── Edges ─────────────────────────────────────────────────────────
    graph.add_edge(START, "architect")

    # Conditional: architect -> inquisitor (loop) OR draft_story (proceed)
    graph.add_conditional_edges(
        "architect",
        route_after_evaluation,
        {
            "inquisitor_node": "inquisitor",
            "draft_story_node": "draft_story",
        },
    )

    # Inquisitor returns the follow-up question → end this invocation
    graph.add_edge("inquisitor", END)

    # Drafting pipeline: draft → comic → meme → done
    graph.add_edge("draft_story", "generate_comic")
    graph.add_edge("generate_comic", "create_meme")
    graph.add_edge("create_meme", END)

    return graph.compile(checkpointer=MemorySaver())


# Module-level compiled graph — import this to execute the workflow.
storyverse_graph = build_workflow()
