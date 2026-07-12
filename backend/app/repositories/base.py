"""
Base repository providing generic CRUD helpers on top of the Supabase SDK.

Every domain repository inherits from BaseRepository and passes in:
  - table_name: the Supabase/PostgreSQL table to operate on
  - client: the per-request user-scoped Supabase Client

Design decisions:
  - All methods are synchronous (Supabase Python SDK v2 is sync).
  - Soft-delete is implemented by filtering deleted_at IS NULL on list/get.
  - company_id is always passed in from the service layer — NOT read from
    the DB client — to maintain a single point of company scoping.
  - Raise DatabaseError on unexpected SDK errors so callers never
    need to handle raw PostgREST exceptions.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.core.logging import logger
from app.exceptions import DatabaseError, NotFoundError


class BaseRepository:
    """Generic Supabase repository with common CRUD operations."""

    def __init__(self, client: Client, table_name: str) -> None:
        self.client = client
        self.table = table_name

    # ── Internal helpers ──────────────────────────────────────

    def _query(self):
        """Return a fresh PostgREST query builder for the table."""
        return self.client.table(self.table)

    def _handle_error(self, operation: str, error: Any) -> None:
        """Log and raise DatabaseError from a Supabase response error."""
        logger.error("DB error | table={} op={} error={}", self.table, operation, error)
        raise DatabaseError(message=f"Database error during {operation}: {error}")

    # ── Core CRUD ─────────────────────────────────────────────

    def get_by_id(
        self,
        record_id: UUID,
        company_id: Optional[UUID] = None,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """
        Fetch a single record by primary key.
        Optionally scope by company_id and exclude soft-deleted rows.
        Raises NotFoundError if the record doesn't exist.
        """
        query = self._query().select("*").eq("id", str(record_id))
        if company_id:
            query = query.eq("company_id", str(company_id))
        if not include_deleted and self._has_soft_delete():
            query = query.is_("deleted_at", "null")

        response = query.single().execute()

        if not response.data:
            raise NotFoundError(resource=self.table.rstrip("s").capitalize(), resource_id=str(record_id))
        return response.data

    def list(
        self,
        company_id: UUID,
        *,
        filters: Optional[Dict[str, Any]] = None,
        search_column: Optional[str] = None,
        search_value: Optional[str] = None,
        order_by: str = "created_at",
        ascending: bool = False,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List records for a company with optional filtering, search, and pagination.
        Returns an empty list if no records match.
        """
        query = self._query().select("*").eq("company_id", str(company_id))

        if not include_deleted and self._has_soft_delete():
            query = query.is_("deleted_at", "null")

        if filters:
            for col, val in filters.items():
                if val is not None:
                    query = query.eq(col, str(val) if isinstance(val, UUID) else val)

        if search_column and search_value:
            query = query.ilike(search_column, f"%{search_value}%")

        query = query.order(order_by, desc=not ascending)
        query = query.range(offset, offset + limit - 1)

        response = query.execute()
        return response.data or []

    def count(
        self,
        company_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> int:
        """Return the total count of matching records (for pagination)."""
        query = (
            self._query()
            .select("id", count="exact")
            .eq("company_id", str(company_id))
        )
        if not include_deleted and self._has_soft_delete():
            query = query.is_("deleted_at", "null")
        if filters:
            for col, val in filters.items():
                if val is not None:
                    query = query.eq(col, str(val) if isinstance(val, UUID) else val)

        response = query.execute()
        return response.count or 0

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new record. Returns the created row.
        `data` should already include company_id where applicable.
        """
        try:
            response = self._query().insert(data).execute()
            if not response.data:
                self._handle_error("create", "No data returned after insert")
            return response.data[0]
        except Exception as exc:
            if isinstance(exc, DatabaseError):
                raise
            self._handle_error("create", str(exc))

    def update(
        self,
        record_id: UUID,
        data: Dict[str, Any],
        company_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Update a record by primary key. Returns the updated row.
        Only non-None values in `data` are applied.
        """
        # Strip None values to avoid overwriting with NULL unintentionally
        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            return self.get_by_id(record_id, company_id)

        try:
            query = self._query().update(update_data).eq("id", str(record_id))
            if company_id:
                query = query.eq("company_id", str(company_id))
            response = query.execute()
            if not response.data:
                raise NotFoundError(
                    resource=self.table.rstrip("s").capitalize(),
                    resource_id=str(record_id),
                )
            return response.data[0]
        except (NotFoundError, DatabaseError):
            raise
        except Exception as exc:
            self._handle_error("update", str(exc))

    def soft_delete(self, record_id: UUID, company_id: Optional[UUID] = None) -> bool:
        """
        Set deleted_at = NOW() on the record.
        Returns True on success. Raises NotFoundError if not found.
        """
        from datetime import datetime, timezone
        try:
            query = (
                self._query()
                .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
                .eq("id", str(record_id))
                .is_("deleted_at", "null")  # Idempotent check
            )
            if company_id:
                query = query.eq("company_id", str(company_id))
            response = query.execute()
            if not response.data:
                raise NotFoundError(
                    resource=self.table.rstrip("s").capitalize(),
                    resource_id=str(record_id),
                )
            return True
        except (NotFoundError, DatabaseError):
            raise
        except Exception as exc:
            self._handle_error("soft_delete", str(exc))

    def hard_delete(self, record_id: UUID, company_id: Optional[UUID] = None) -> bool:
        """
        Permanently delete a record. Use with caution — prefer soft_delete.
        """
        try:
            query = self._query().delete().eq("id", str(record_id))
            if company_id:
                query = query.eq("company_id", str(company_id))
            query.execute()
            return True
        except Exception as exc:
            self._handle_error("hard_delete", str(exc))

    # ── Helpers ───────────────────────────────────────────────

    def _has_soft_delete(self) -> bool:
        """
        Tables that use soft-delete have a deleted_at column.
        Override in subclasses that do NOT use soft-delete to skip the filter.
        """
        SOFT_DELETE_TABLES = {
            "companies", "branches", "customers", "suppliers", "categories",
            "products", "warehouses", "sales", "purchases", "invoices",
            "expenses", "chat_sessions", "reports", "integrations",
        }
        return self.table in SOFT_DELETE_TABLES
