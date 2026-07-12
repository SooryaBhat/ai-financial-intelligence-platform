"""
Request context dataclass.
Injected into all service calls to provide user, company, and
request metadata without requiring each method to accept them individually.
"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from supabase import Client


@dataclass
class RequestContext:
    """
    Carries per-request contextual data:
      - user_id: authenticated caller's UUID
      - company_id: active company for this request
      - user_client: Supabase client authenticating as the caller (RLS enforced)
      - ip_address: caller's IP (for audit logs)
      - user_agent: caller's user agent (for audit logs)
    """
    user_id: UUID
    company_id: UUID
    user_client: Client
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    role_id: Optional[UUID] = None
    permissions: list = field(default_factory=list)
