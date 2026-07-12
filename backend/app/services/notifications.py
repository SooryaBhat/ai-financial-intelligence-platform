"""Notifications service."""
from typing import Any, Dict, List
from uuid import UUID

from app.database.client import get_admin_client
from app.repositories.notifications import NotificationRepository
from app.schemas.notifications import NotificationCreate
from app.services.context import RequestContext
from app.core.constants import NotificationType


class NotificationService:
    def __init__(self, repo: NotificationRepository) -> None:
        self._repo = repo

    def list_for_user(self, ctx: RequestContext, unread_only: bool = False) -> List[Dict[str, Any]]:
        return self._repo.list_for_user(ctx.company_id, ctx.user_id, unread_only)

    def count_unread(self, ctx: RequestContext) -> int:
        return self._repo.count_unread(ctx.company_id, ctx.user_id)

    def mark_read(self, notification_ids: List[UUID], ctx: RequestContext) -> None:
        self._repo.mark_read(notification_ids, ctx.user_id)

    def send(
        self,
        company_id: UUID,
        user_id: UUID,
        ntype: NotificationType,
        title: str,
        message: str = None,
        action_url: str = None,
    ) -> Dict[str, Any]:
        """Internal method to create a notification — uses admin client."""
        admin_repo = NotificationRepository(get_admin_client())
        return admin_repo.create({
            "company_id": str(company_id),
            "user_id": str(user_id),
            "type": ntype.value,
            "title": title,
            "message": message,
            "action_url": action_url,
        })
