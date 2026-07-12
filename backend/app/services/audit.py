"""
Audit service — writes entries to the audit_logs table.
Uses the ADMIN client (service role) so it can always write audit logs
even if the user's RLS would block it.

Design: The audit service is called explicitly from service layer methods
after every mutating operation. This gives us full control over what is
logged versus letting triggers do it blindly.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.constants import AuditAction
from app.core.logging import logger
from app.database.client import get_admin_client
from app.repositories.audit_logs import AuditLogRepository


class AuditService:
    """Writes immutable audit log entries."""

    def __init__(self) -> None:
        # Always use the admin client for audit writes — never block on RLS
        self._repo = AuditLogRepository(get_admin_client())

    def log(
        self,
        company_id: UUID,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Write a single audit log entry. Never raises — swallows exceptions to avoid
        breaking the primary operation if the audit write fails."""
        try:
            self._repo.create_log({
                "company_id": str(company_id),
                "user_id": str(user_id) if user_id else None,
                "action": action.value,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "old_values": old_values,
                "new_values": new_values,
                "ip_address": ip_address,
                "user_agent": user_agent,
            })
        except Exception as exc:
            logger.error("AuditService.log failed: {}", str(exc))

    def log_create(self, company_id: UUID, resource_type: str, resource_id: UUID,
                   new_values: Dict, user_id: Optional[UUID] = None,
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        self.log(company_id, AuditAction.CREATE, resource_type, resource_id,
                 user_id, None, new_values, ip_address, user_agent)

    def log_update(self, company_id: UUID, resource_type: str, resource_id: UUID,
                   old_values: Dict, new_values: Dict, user_id: Optional[UUID] = None,
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        self.log(company_id, AuditAction.UPDATE, resource_type, resource_id,
                 user_id, old_values, new_values, ip_address, user_agent)

    def log_delete(self, company_id: UUID, resource_type: str, resource_id: UUID,
                   old_values: Dict, user_id: Optional[UUID] = None,
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        self.log(company_id, AuditAction.DELETE, resource_type, resource_id,
                 user_id, old_values, None, ip_address, user_agent)


# Module-level singleton
audit_service = AuditService()
