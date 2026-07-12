"""Payments repository."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "payments")

    def list_by_invoice(self, invoice_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("invoice_id", str(invoice_id))
            .order("payment_date", desc=True)
            .execute()
        )
        return response.data or []

    def sum_payments_for_invoice(self, invoice_id: UUID) -> float:
        response = (
            self._query()
            .select("amount")
            .eq("invoice_id", str(invoice_id))
            .execute()
        )
        return sum(row["amount"] for row in (response.data or []))
