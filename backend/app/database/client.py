"""
Supabase client factory.

Three client types:
  1. get_anon_client()          - anon key, used for auth operations
  2. get_admin_client()         - service role, bypasses RLS (admin only)
  3. get_user_client(jwt)       - user JWT, enforces RLS (primary client)

Always prefer get_user_client() for user-facing operations so that
Supabase RLS policies automatically enforce multi-tenancy isolation.
"""
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings
from app.core.logging import logger


@lru_cache(maxsize=1)
def get_anon_client() -> Client:
    """
    Return a cached Supabase client using the anon key.
    Used for: signup, login, and public operations.
    """
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    logger.debug("Anon Supabase client created")
    return client


@lru_cache(maxsize=1)
def get_admin_client() -> Client:
    """
    Return a cached Supabase admin client using the service role key.
    WARNING: This bypasses ALL Row Level Security policies.
    Use ONLY for:
      - Admin operations
      - Background jobs
      - Seeding / migrations
    Never expose this client's output directly to end users.
    """
    client = create_client(
        settings.supabase_url, settings.supabase_service_role_key
    )
    logger.debug("Admin Supabase client created (service role)")
    return client


def get_user_client(jwt: str) -> Client:
    """
    Create a per-request Supabase client that authenticates as the caller.
    The user's JWT is injected so Supabase enforces RLS policies on every
    query — multi-tenancy is handled at the DB layer, not in application code.

    Args:
        jwt: The raw Bearer token from the Authorization header.

    Returns:
        An authenticated Supabase Client instance.
    """
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(jwt)
    return client
