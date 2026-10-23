"""
Import executor service.
Executes confirmed validated batches into Supabase under strict multi-tenant isolation,
idempotency protection, and entity-specific relational workflows.
"""
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid
from uuid import UUID

from app.core.logging import logger
from app.exceptions import ConflictError, ValidationError
from app.repositories.inventory import InventoryRepository, StockMovementRepository
from app.schemas.inventory import AdjustInventoryRequest
from app.services.audit import audit_service
from app.services.context import RequestContext
from app.services.inventory import InventoryService

# In-memory batch store & idempotency cache
_BATCH_CACHE: Dict[str, Dict[str, Any]] = {}
_IDEMPOTENCY_CACHE: Dict[str, Dict[str, Any]] = {}


class ImportExecutor:
    def __init__(self, ctx: RequestContext) -> None:
        self.ctx = ctx

    def execute_batch(
        self,
        entity_type: str,
        validated_rows: List[Dict[str, Any]],
        conflict_policy: str = "skip",  # "skip" or "update"
        idempotency_key: Optional[str] = None,
        file_name: str = "imported_file",
        source_format: str = "csv",
    ) -> Dict[str, Any]:
        """
        Execute confirmed batch records.
        Applies idempotency check, tenant isolation, and conflict policies.
        """
        # 1. Idempotency Check
        if idempotency_key:
            cache_key = f"{self.ctx.company_id}:{idempotency_key}"
            if cache_key in _IDEMPOTENCY_CACHE:
                logger.info(
                    "Idempotent import request matched | company={} idempotency_key={}",
                    self.ctx.company_id,
                    idempotency_key,
                )
                return _IDEMPOTENCY_CACHE[cache_key]

        batch_id = str(uuid.uuid4())
        valid_items = [
            r["normalized_data"]
            for r in validated_rows
            if r.get("status") in ("valid", "warning") and r.get("normalized_data")
        ]

        if not valid_items:
            raise ValidationError("No valid rows available to import.")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        errors: List[str] = []

        try:
            if entity_type == "products":
                c, u, s, f, errs = self._execute_products(valid_items, conflict_policy)
            elif entity_type == "sales":
                c, u, s, f, errs = self._execute_sales(valid_items, conflict_policy)
            elif entity_type == "inventory":
                c, u, s, f, errs = self._execute_inventory(valid_items)
            elif entity_type == "expenses":
                c, u, s, f, errs = self._execute_expenses(valid_items)
            elif entity_type == "invoices":
                c, u, s, f, errs = self._execute_invoices(valid_items, conflict_policy)
            else:
                raise ValueError(f"Unknown entity type '{entity_type}'")

            created_count += c
            updated_count += u
            skipped_count += s
            failed_count += f
            errors.extend(errs)
            status = "completed" if failed_count == 0 else ("completed" if (created_count + updated_count) > 0 else "failed")
        except Exception as e:
            logger.error("Import execution failed | company={} error={}", self.ctx.company_id, str(e))
            status = "failed"
            errors.append(f"Import failed: {str(e)}")

        result_summary = {
            "batch_id": batch_id,
            "company_id": str(self.ctx.company_id),
            "entity_type": entity_type,
            "file_name": file_name,
            "source_format": source_format,
            "status": status,
            "total_submitted": len(validated_rows),
            "created_count": created_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "errors": errors,
            "idempotency_key": idempotency_key,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Cache in memory
        _BATCH_CACHE[batch_id] = result_summary
        if idempotency_key:
            _IDEMPOTENCY_CACHE[f"{self.ctx.company_id}:{idempotency_key}"] = result_summary

        # Try persisting to database import_batches table if migration has been executed
        self._persist_batch_record(result_summary)

        return result_summary

    def _persist_batch_record(self, summary: Dict[str, Any]) -> None:
        """Attempt to record to import_batches table; gracefully falls back if table does not exist."""
        try:
            self.ctx.user_client.table("import_batches").insert({
                "id": summary["batch_id"],
                "company_id": str(self.ctx.company_id),
                "branch_id": str(self.ctx.branch_id) if self.ctx.branch_id else None,
                "created_by": str(self.ctx.user_id) if self.ctx.user_id else None,
                "entity_type": summary["entity_type"],
                "source_format": summary.get("source_format", "csv"),
                "file_name": summary.get("file_name", "unknown"),
                "total_rows": summary["total_submitted"],
                "valid_rows": summary["created_count"] + summary["updated_count"] + summary["skipped_count"],
                "imported_rows": summary["created_count"] + summary["updated_count"],
                "status": summary["status"],
                "idempotency_key": summary.get("idempotency_key"),
                "summary_details": summary,
            }).execute()
        except Exception:
            # Table might not exist yet if migration has not been applied; batch remains in cache
            pass

    # ─────────────────────────────────────────────────────────────
    # Entity Implementations
    # ─────────────────────────────────────────────────────────────

    def _execute_products(
        self, items: List[Dict[str, Any]], conflict_policy: str
    ) -> Tuple[int, int, int, int, List[str]]:
        created = 0
        updated = 0
        skipped = 0
        failed = 0
        errors: List[str] = []

        # Fetch existing products
        res = (
            self.ctx.user_client.table("products")
            .select("id, sku")
            .eq("company_id", str(self.ctx.company_id))
            .is_("deleted_at", "null")
            .execute()
        )
        existing_by_sku = {p["sku"].strip().upper(): p["id"] for p in (res.data or []) if p.get("sku")}

        for item in items:
            try:
                sku = item.get("sku")
                upper_sku = sku.strip().upper() if sku else None

                product_payload = {
                    "company_id": str(self.ctx.company_id),
                    "name": item["name"],
                    "sku": item.get("sku"),
                    "cost_price": float(item.get("cost_price", 0.0)),
                    "selling_price": float(item.get("selling_price", 0.0)),
                    "tax_rate": float(item.get("tax_rate", 0.0)),
                    "unit": item.get("unit") or "pcs",
                    "type": item.get("type") or "product",
                    "description": item.get("description"),
                    "is_active": True,
                }

                if upper_sku and upper_sku in existing_by_sku:
                    if conflict_policy == "update":
                        prod_id = existing_by_sku[upper_sku]
                        self.ctx.user_client.table("products").update(product_payload).eq("id", prod_id).execute()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    self.ctx.user_client.table("products").insert(product_payload).execute()
                    created += 1
                    if upper_sku:
                        existing_by_sku[upper_sku] = "created"
            except Exception as e:
                failed += 1
                errors.append(f"Product '{item.get('name')}': {str(e)}")

        return created, updated, skipped, failed, errors

    def _execute_sales(
        self, items: List[Dict[str, Any]], conflict_policy: str
    ) -> Tuple[int, int, int, int, List[str]]:
        created = 0
        updated = 0
        skipped = 0
        failed = 0
        errors: List[str] = []

        # Group line items by sale_number
        orders: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for item in items:
            orders[item["sale_number"]].append(item)

        for sale_number, line_items in orders.items():
            try:
                # Check if sale already exists
                res = (
                    self.ctx.user_client.table("sales")
                    .select("id, sale_number")
                    .eq("company_id", str(self.ctx.company_id))
                    .eq("sale_number", sale_number)
                    .execute()
                )
                existing_sale = res.data[0] if res.data else None

                if existing_sale:
                    if conflict_policy == "skip":
                        skipped += len(line_items)
                        continue
                    sale_id = existing_sale["id"]
                    # Append items to existing sale
                    sale_items_payload = []
                    for line in line_items:
                        sale_items_payload.append({
                            "sale_id": sale_id,
                            "product_id": line["product_id"],
                            "quantity": line["quantity"],
                            "unit_price": line["unit_price"],
                            "discount_pct": line.get("discount_pct", 0.0),
                            "tax_rate": line.get("tax_rate", 0.0),
                            "line_total": line.get("line_total", line["quantity"] * line["unit_price"]),
                        })
                    self.ctx.user_client.table("sale_items").insert(sale_items_payload).execute()
                    updated += 1
                else:
                    # Calculate totals for new sale
                    subtotal = sum(l["quantity"] * l["unit_price"] for l in line_items)
                    discount_amount = sum(
                        (l["quantity"] * l["unit_price"]) * (l.get("discount_pct", 0.0) / 100.0)
                        for l in line_items
                    )
                    tax_amount = sum(
                        ((l["quantity"] * l["unit_price"]) - ((l["quantity"] * l["unit_price"]) * (l.get("discount_pct", 0.0) / 100.0)))
                        * (l.get("tax_rate", 0.0) / 100.0)
                        for l in line_items
                    )
                    total_amount = round(subtotal - discount_amount + tax_amount, 2)

                    first_line = line_items[0]
                    sale_payload = {
                        "company_id": str(self.ctx.company_id),
                        "branch_id": str(self.ctx.branch_id) if self.ctx.branch_id else None,
                        "sale_number": sale_number,
                        "sale_date": first_line.get("sale_date", str(date.today())),
                        "currency": "USD",
                        "status": "confirmed",
                        "subtotal": round(subtotal, 2),
                        "discount_amount": round(discount_amount, 2),
                        "tax_amount": round(tax_amount, 2),
                        "total_amount": total_amount,
                        "notes": first_line.get("notes"),
                        "created_by": str(self.ctx.user_id) if self.ctx.user_id else None,
                    }

                    sale_res = self.ctx.user_client.table("sales").insert(sale_payload).execute()
                    new_sale = sale_res.data[0]
                    sale_id = new_sale["id"]

                    # Insert line items
                    sale_items_payload = []
                    for line in line_items:
                        sale_items_payload.append({
                            "sale_id": sale_id,
                            "product_id": line["product_id"],
                            "quantity": line["quantity"],
                            "unit_price": line["unit_price"],
                            "discount_pct": line.get("discount_pct", 0.0),
                            "tax_rate": line.get("tax_rate", 0.0),
                            "line_total": line.get("line_total", line["quantity"] * line["unit_price"]),
                        })
                    self.ctx.user_client.table("sale_items").insert(sale_items_payload).execute()
                    created += 1

            except Exception as e:
                failed += len(line_items)
                errors.append(f"Sale '{sale_number}': {str(e)}")

        return created, updated, skipped, failed, errors

    def _execute_inventory(self, items: List[Dict[str, Any]]) -> Tuple[int, int, int, int, List[str]]:
        created = 0
        updated = 0
        skipped = 0
        failed = 0
        errors: List[str] = []

        inv_service = InventoryService(
            InventoryRepository(self.ctx.user_client),
            StockMovementRepository(self.ctx.user_client),
        )

        for item in items:
            try:
                product_id = UUID(item["product_id"])
                warehouse_id = UUID(item["warehouse_id"])
                delta = float(item["quantity_delta"])

                if delta == 0:
                    skipped += 1
                    continue

                req = AdjustInventoryRequest(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity_delta=delta,
                    notes=item.get("notes") or "CSV/Excel import adjustment",
                )
                inv_service.adjust_stock(req, self.ctx)
                created += 1
            except Exception as e:
                failed += 1
                errors.append(f"Inventory SKU '{item.get('product_sku')}': {str(e)}")

        return created, updated, skipped, failed, errors

    def _execute_expenses(self, items: List[Dict[str, Any]]) -> Tuple[int, int, int, int, List[str]]:
        created = 0
        updated = 0
        skipped = 0
        failed = 0
        errors: List[str] = []

        for item in items:
            try:
                payload = {
                    "company_id": str(self.ctx.company_id),
                    "branch_id": str(self.ctx.branch_id) if self.ctx.branch_id else None,
                    "created_by": str(self.ctx.user_id) if self.ctx.user_id else None,
                    "description": item["description"],
                    "amount": float(item["amount"]),
                    "expense_date": item.get("expense_date", str(date.today())),
                    "payment_method": item.get("payment_method") or "cash",
                    "status": "pending",
                    "notes": item.get("notes"),
                }
                self.ctx.user_client.table("expenses").insert(payload).execute()
                created += 1
            except Exception as e:
                failed += 1
                errors.append(f"Expense '{item.get('description')}': {str(e)}")

        return created, updated, skipped, failed, errors

    def _execute_invoices(
        self, items: List[Dict[str, Any]], conflict_policy: str
    ) -> Tuple[int, int, int, int, List[str]]:
        created = 0
        updated = 0
        skipped = 0
        failed = 0
        errors: List[str] = []

        # Check existing invoices
        res = (
            self.ctx.user_client.table("invoices")
            .select("id, invoice_number")
            .eq("company_id", str(self.ctx.company_id))
            .is_("deleted_at", "null")
            .execute()
        )
        existing_by_num = {i["invoice_number"].strip().upper(): i["id"] for i in (res.data or []) if i.get("invoice_number")}

        for item in items:
            try:
                num = item["invoice_number"]
                upper_num = num.strip().upper()

                payload = {
                    "company_id": str(self.ctx.company_id),
                    "invoice_number": num,
                    "invoice_type": item.get("invoice_type") or "receivable",
                    "invoice_date": item.get("invoice_date", str(date.today())),
                    "due_date": item.get("due_date"),
                    "subtotal": float(item.get("subtotal", item.get("total_amount", 0.0))),
                    "tax_amount": float(item.get("tax_amount", 0.0)),
                    "total_amount": float(item["total_amount"]),
                    "currency": "USD",
                    "status": "draft",
                    "notes": item.get("notes"),
                }

                if upper_num in existing_by_num:
                    if conflict_policy == "update":
                        inv_id = existing_by_num[upper_num]
                        self.ctx.user_client.table("invoices").update(payload).eq("id", inv_id).execute()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    self.ctx.user_client.table("invoices").insert(payload).execute()
                    created += 1
                    existing_by_num[upper_num] = "created"

            except Exception as e:
                failed += 1
                errors.append(f"Invoice '{item.get('invoice_number')}': {str(e)}")

        return created, updated, skipped, failed, errors
