"""Expenses repository."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "expenses")

    def list_pending_approval(self, company_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*, categories(name), users!expenses_created_by_fkey(full_name)")
            .eq("company_id", str(company_id))
            .eq("status", "pending")
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def approve(self, expense_id: UUID, approver_id: UUID, status: str) -> Dict[str, Any]:
        response = (
            self._query()
            .update({"status": status, "approved_by": str(approver_id)})
            .eq("id", str(expense_id))
            .execute()
        )
        return response.data[0] if response.data else {}
