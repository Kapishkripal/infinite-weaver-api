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

import os

from graph.state import StoryverseState
from services.story_engine import (
    evaluate_world_bible,
    generate_follow_up_question,
    draft_chapter,
)
from services.comic_engine import generate_scene_prompt, generate_image
from services.meme_engine import extract_humorous_quote, assemble_meme
from core.db import supabase


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
            "prompt": state.get("user_input", "An Epic Tale"),
            "story_text": chapter_text,
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
    """Turn the story draft into comic-panel images."""
    print("[node] generate_comic — generating comic panel")
    
    story_draft = state.get("story_draft", "")
    
    # Extract prompt
    scene_prompt = generate_scene_prompt(story_draft)
    
    # Generate image
    image_path = generate_image(scene_prompt, filename="comic_raw.jpg")
    
    paths = state.get("image_paths", [])
    if image_path:
        paths.append(image_path)
        
    return {"image_paths": paths}


def create_meme(state: StoryverseState) -> dict:
    """Produce shareable meme assets from the story content and upload to Supabase."""
    print("[node] create_meme — assembling meme")
    
    story_draft = state.get("story_draft", "")
    paths = state.get("image_paths", [])
    user_id = state.get("user_id", "anonymous")
    
    if not paths:
        print("[node] create_meme — No images available to meme.")
        return {}
        
    raw_comic_path = paths[-1] # use the last generated image
    
    # Extract quotes
    top_text, bottom_text = extract_humorous_quote(story_draft)
    
    # Assemble meme
    meme_path = assemble_meme(raw_comic_path, top_text, bottom_text, filename="meme_final.jpg")
    if meme_path:
        paths.append(meme_path)
        
    # --- Upload to Supabase Storage ---
    print("[node] create_meme — Uploading to Supabase...")
    bucket_name = "media"
    comic_url = ""
    meme_url = ""
    
    try:
        # Upload Comic
        if os.path.exists(raw_comic_path):
            comic_dest = f"{user_id}/comic_{os.path.basename(raw_comic_path)}"
            with open(raw_comic_path, "rb") as f:
                supabase.storage.from_(bucket_name).upload(comic_dest, f, {"upsert": "true"})
            comic_url = supabase.storage.from_(bucket_name).get_public_url(comic_dest)
            
        # Upload Meme
        if os.path.exists(meme_path):
            meme_dest = f"{user_id}/meme_{os.path.basename(meme_path)}"
            with open(meme_path, "rb") as f:
                supabase.storage.from_(bucket_name).upload(meme_dest, f, {"upsert": "true"})
            meme_url = supabase.storage.from_(bucket_name).get_public_url(meme_dest)
            
        print("[node] create_meme — Upload complete. Updating database.")
        
        # Update Database
        supabase.table("stories").update({
            "comic_url": comic_url,
            "meme_url": meme_url
        }).eq("user_id", user_id).eq("prompt", state.get("user_input", "An Epic Tale")).execute()
        
    except Exception as e:
        print(f"[node] create_meme — Supabase upload/update failed: {e}")
        
    # Clean up local files
    for p in [raw_comic_path, meme_path]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass
                
    # We return the public URLs in image_paths so the client gets them
    final_paths = []
    if comic_url: final_paths.append(comic_url)
    if meme_url: final_paths.append(meme_url)
    
    return {"image_paths": final_paths}


# ---------------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------------


def route_after_evaluation(state: StoryverseState) -> str:
    """Route based on the Architect's clarity score.

    Returns a routing key that maps to a registered node name
    in the conditional edge dictionary.
    """
    current_score = state.get("clarity_score", 0)
    target = state.get("target_score", 80) # Fallback to 80 if missing

    print(f"[router] Current clarity: {current_score}%, Target threshold: {target}%")

    if current_score >= target:
        return "draft_story_node"
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
