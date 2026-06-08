"""
main.py — Storyverse API entry-point.

Launches the FastAPI application and mounts all routers.

Run with:
    uvicorn main:app --reload
"""

from fastapi import FastAPI

from api.generate import router as generate_router

app = FastAPI(
    title="Storyverse API",
    description=(
        "AI-powered creative pipeline that interviews users, drafts stories, "
        "generates comic panels, and creates memes — orchestrated by LangGraph."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Mount routers
# ---------------------------------------------------------------------------
app.include_router(generate_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["ops"])
async def health():
    """Lightweight liveness probe."""
    return {"status": "ok"}
