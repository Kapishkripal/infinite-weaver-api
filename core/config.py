"""
core/config.py — Centralised environment configuration.

Loads all required environment variables from the project-root .env
file and raises eagerly if any are missing.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Required variables
# ---------------------------------------------------------------------------

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")

_missing = [
    name
    for name, val in [
        ("SUPABASE_URL", SUPABASE_URL),
        ("SUPABASE_KEY", SUPABASE_KEY),
        ("GOOGLE_API_KEY", GOOGLE_API_KEY),
    ]
    if not val
]

if _missing:
    raise ValueError(
        f"Missing required environment variable(s): {', '.join(_missing)}. "
        "Please set them in your .env file."
    )
