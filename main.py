"""
main.py — Storyverse API entry-point.

Launches the FastAPI application and mounts all routers.

Run with:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
# Configure CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (Vercel, localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS)
    allow_headers=["*"],
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
