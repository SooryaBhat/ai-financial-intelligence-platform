"""Invoices repository."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "invoices")

    def list_overdue(self, company_id: UUID) -> List[Dict[str, Any]]:
        from datetime import date
        today = date.today().isoformat()
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .neq("status", "paid")
            .neq("status", "cancelled")
            .lt("due_date", today)
            .is_("deleted_at", "null")
            .execute()
        )
        return response.data or []

    def update_amount_paid(self, invoice_id: UUID, company_id: UUID, amount_paid: float) -> Dict[str, Any]:
        response = (
            self._query()
            .update({"amount_paid": amount_paid})
            .eq("id", str(invoice_id))
            .eq("company_id", str(company_id))
            .execute()
        )
        return response.data[0] if response.data else {}

    def get_by_number(self, company_id: UUID, invoice_number: str) -> Any:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("invoice_number", invoice_number)
            .execute()
        )
        return response.data[0] if response.data else None
