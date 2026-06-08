"""
core/db.py — Supabase client initialization.

Imports credentials from the centralised config module and exposes
a ready-to-use `supabase` client singleton.
"""

from supabase import create_client, Client

from core.config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
