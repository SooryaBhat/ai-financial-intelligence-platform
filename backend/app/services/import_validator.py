"""
Import validator service.
Validates normalized records against ERP business rules, required fields,
numeric constraints, enum memberships, duplicate detection, and referential integrity
without writing to the database.
"""
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from app.core.constants import (
    ExpenseStatus,
    InvoiceType,
    PaymentMethod,
    ProductType,
)
from app.services.context import RequestContext
from app.services.import_normalizer import ENTITY_SCHEMAS, ImportNormalizer


class ImportValidator:
    def __init__(self, ctx: RequestContext) -> None:
        self.ctx = ctx
        self.normalizer = ImportNormalizer()

    def _get_existing_product_skus(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all existing products for the company keyed by uppercase SKU."""
        try:
            res = (
                self.ctx.user_client.table("products")
                .select("id, name, sku, cost_price, selling_price, type")
                .eq("company_id", str(self.ctx.company_id))
                .is_("deleted_at", "null")
                .execute()
            )
            data = res.data or []
            return {p["sku"].strip().upper(): p for p in data if p.get("sku")}
        except Exception:
            return {}

    def _get_existing_warehouses(self) -> Dict[str, Dict[str, Any]]:
        """Fetch warehouses for the company keyed by uppercase name."""
        try:
            res = (
                self.ctx.user_client.table("warehouses")
                .select("id, name, code")
                .eq("company_id", str(self.ctx.company_id))
                .execute()
            )
            data = res.data or []
            warehouses: Dict[str, Dict[str, Any]] = {}
            for w in data:
                if w.get("name"):
                    warehouses[w["name"].strip().upper()] = w
                if w.get("code"):
                    warehouses[w["code"].strip().upper()] = w
            return warehouses
        except Exception:
            return {}

    def _get_existing_sale_numbers(self) -> Set[str]:
        """Fetch existing sale numbers for company."""
        try:
            res = (
                self.ctx.user_client.table("sales")
                .select("sale_number")
                .eq("company_id", str(self.ctx.company_id))
                .is_("deleted_at", "null")
                .execute()
            )
            return {s["sale_number"].strip().upper() for s in (res.data or []) if s.get("sale_number")}
        except Exception:
            return set()

    def _get_existing_invoice_numbers(self) -> Set[str]:
        """Fetch existing invoice numbers for company."""
        try:
            res = (
                self.ctx.user_client.table("invoices")
                .select("invoice_number")
                .eq("company_id", str(self.ctx.company_id))
                .is_("deleted_at", "null")
                .execute()
            )
            return {i["invoice_number"].strip().upper() for i in (res.data or []) if i.get("invoice_number")}
        except Exception:
            return set()

    def validate_batch(
        self,
        entity_type: str,
        raw_rows: List[Dict[str, Any]],
        column_mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Validate mapped rows against the target schema and ERP database.
        Returns detailed summary and row-level diagnostics.
        """
        schema = self.normalizer.get_entity_schema(entity_type)
        required_fields = {f["name"] for f in schema["fields"] if f.get("required")}

        # Reverse mapping: destination_field -> source_header
        dest_to_source: Dict[str, str] = {dest: src for src, dest in column_mapping.items() if dest}

        # Check required fields are mapped
        missing_required_mappings = required_fields - set(dest_to_source.keys())
        if missing_required_mappings:
            missing_labels = [
                next((f["label"] for f in schema["fields"] if f["name"] == mf), mf)
                for mf in missing_required_mappings
            ]
            return {
                "valid": False,
                "error": f"Required fields missing from column mapping: {', '.join(missing_labels)}",
                "total_rows": len(raw_rows),
                "valid_rows": 0,
                "warning_rows": 0,
                "invalid_rows": len(raw_rows),
                "duplicate_rows": 0,
                "row_results": [],
            }

        # Dispatch entity validation
        if entity_type == "products":
            return self._validate_products(raw_rows, dest_to_source)
        elif entity_type == "sales":
            return self._validate_sales(raw_rows, dest_to_source)
        elif entity_type == "inventory":
            return self._validate_inventory(raw_rows, dest_to_source)
        elif entity_type == "expenses":
            return self._validate_expenses(raw_rows, dest_to_source)
        elif entity_type == "invoices":
            return self._validate_invoices(raw_rows, dest_to_source)
        else:
            raise ValueError(f"Unsupported entity type for validation: '{entity_type}'")

    # ─────────────────────────────────────────────────────────────
    # Entity Validators
    # ─────────────────────────────────────────────────────────────

    def _validate_products(
        self, raw_rows: List[Dict[str, Any]], mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        existing_products = self._get_existing_product_skus()
        file_skus: Set[str] = set()

        row_results: List[Dict[str, Any]] = []
        valid_count = 0
        warning_count = 0
        invalid_count = 0
        duplicate_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            errors: List[str] = []
            warnings: List[str] = []
            norm: Dict[str, Any] = {}

            # Name (required)
            raw_name = row.get(mapping.get("name", ""))
            clean_name = self.normalizer.clean_str(raw_name)
            if not clean_name:
                errors.append("Product name is required.")
            else:
                norm["name"] = clean_name

            # SKU (optional but uniqueness checked)
            raw_sku = row.get(mapping.get("sku", ""))
            clean_sku = self.normalizer.clean_str(raw_sku)
            if clean_sku:
                norm["sku"] = clean_sku
                upper_sku = clean_sku.upper()
                if upper_sku in file_skus:
                    errors.append(f"Duplicate SKU '{clean_sku}' found multiple times in upload file.")
                    duplicate_count += 1
                else:
                    file_skus.add(upper_sku)

                if upper_sku in existing_products:
                    warnings.append(
                        f"SKU '{clean_sku}' already exists in your catalog (will update if update policy selected, or skip)."
                    )
            else:
                norm["sku"] = None
                warnings.append("No SKU provided; automatic SKU will be recommended.")

            # Selling Price (required, >= 0)
            raw_sp = row.get(mapping.get("selling_price", ""))
            sp, sp_err = self.normalizer.normalize_number(raw_sp, min_val=0.0)
            if sp_err:
                errors.append(f"Selling price: {sp_err}")
            elif sp is None:
                errors.append("Selling price is required.")
            else:
                norm["selling_price"] = sp

            # Cost Price (optional, >= 0)
            raw_cp = row.get(mapping.get("cost_price", ""))
            cp, cp_err = self.normalizer.normalize_number(raw_cp, default=0.0, min_val=0.0)
            if cp_err:
                errors.append(f"Cost price: {cp_err}")
            else:
                norm["cost_price"] = cp

            # Tax Rate (optional, 0 to 100)
            raw_tr = row.get(mapping.get("tax_rate", ""))
            tr, tr_err = self.normalizer.normalize_number(raw_tr, default=0.0, min_val=0.0, max_val=100.0)
            if tr_err:
                errors.append(f"Tax rate: {tr_err}")
            else:
                norm["tax_rate"] = tr

            # Category
            raw_cat = row.get(mapping.get("category", ""))
            norm["category"] = self.normalizer.clean_str(raw_cat)

            # Unit
            raw_unit = row.get(mapping.get("unit", ""))
            norm["unit"] = self.normalizer.clean_str(raw_unit) or "pcs"

            # Type
            raw_type = row.get(mapping.get("type", ""))
            ptype, type_err = self.normalizer.normalize_enum(raw_type, ProductType, default=ProductType.PRODUCT)
            if type_err:
                warnings.append(f"Type: {type_err}. Defaulted to 'product'.")
            norm["type"] = ptype.value if hasattr(ptype, "value") else "product"

            # Description
            raw_desc = row.get(mapping.get("description", ""))
            norm["description"] = self.normalizer.clean_str(raw_desc)

            # Determine status
            is_conflict = clean_sku and clean_sku.upper() in existing_products
            if errors:
                status = "invalid"
                invalid_count += 1
                action = "error"
            elif warnings:
                status = "warning"
                warning_count += 1
                valid_count += 1
                action = "update" if is_conflict else "create"
            else:
                status = "valid"
                valid_count += 1
                action = "create"

            row_results.append({
                "row_number": idx,
                "status": status,
                "source_data": row,
                "normalized_data": norm,
                "errors": errors,
                "warnings": warnings,
                "is_conflict": bool(is_conflict),
                "action_proposed": action,
            })

        return {
            "valid": invalid_count == 0,
            "total_rows": len(raw_rows),
            "valid_rows": valid_count,
            "warning_rows": warning_count,
            "invalid_rows": invalid_count,
            "duplicate_rows": duplicate_count,
            "row_results": row_results,
        }

    def _validate_sales(
        self, raw_rows: List[Dict[str, Any]], mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        existing_products = self._get_existing_product_skus()
        existing_sales = self._get_existing_sale_numbers()
        seen_order_lines: Set[Tuple[str, str]] = set()

        row_results: List[Dict[str, Any]] = []
        valid_count = 0
        warning_count = 0
        invalid_count = 0
        duplicate_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            errors: List[str] = []
            warnings: List[str] = []
            norm: Dict[str, Any] = {}

            # Sale Number (required)
            raw_num = row.get(mapping.get("sale_number", ""))
            clean_num = self.normalizer.clean_str(raw_num)
            if not clean_num:
                errors.append("Sale / order number is required.")
            else:
                norm["sale_number"] = clean_num
                if clean_num.upper() in existing_sales:
                    warnings.append(
                        f"Sale #{clean_num} already exists in database. Line items will be appended if approved."
                    )

            # Product SKU (required)
            raw_sku = row.get(mapping.get("product_sku", ""))
            clean_sku = self.normalizer.clean_str(raw_sku)
            if not clean_sku:
                errors.append("Product SKU is required for line item.")
            else:
                norm["product_sku"] = clean_sku
                upper_sku = clean_sku.upper()
                if upper_sku not in existing_products:
                    errors.append(
                        f"Referenced product with SKU '{clean_sku}' does not exist in your company catalog. Import products first."
                    )
                else:
                    norm["product_id"] = existing_products[upper_sku]["id"]

            # Line duplicate check
            if clean_num and clean_sku:
                line_key = (clean_num.upper(), clean_sku.upper())
                if line_key in seen_order_lines:
                    warnings.append(f"Multiple lines for SKU '{clean_sku}' under order '{clean_num}'.")
                    duplicate_count += 1
                seen_order_lines.add(line_key)

            # Quantity (required, > 0)
            raw_qty = row.get(mapping.get("quantity", ""))
            qty, qty_err = self.normalizer.normalize_number(raw_qty, min_val=0.001)
            if qty_err:
                errors.append(f"Quantity: {qty_err}")
            elif qty is None or qty <= 0:
                errors.append("Quantity must be greater than 0.")
            else:
                norm["quantity"] = qty

            # Unit Price (required, >= 0)
            raw_price = row.get(mapping.get("unit_price", ""))
            price, price_err = self.normalizer.normalize_number(raw_price, min_val=0.0)
            if price_err:
                errors.append(f"Unit price: {price_err}")
            elif price is None:
                errors.append("Unit price is required.")
            else:
                norm["unit_price"] = price

            # Discount Pct (optional, 0 to 100)
            raw_disc = row.get(mapping.get("discount_pct", ""))
            disc, disc_err = self.normalizer.normalize_number(raw_disc, default=0.0, min_val=0.0, max_val=100.0)
            if disc_err:
                errors.append(f"Discount: {disc_err}")
            else:
                norm["discount_pct"] = disc

            # Tax Rate (optional, 0 to 100)
            raw_tax = row.get(mapping.get("tax_rate", ""))
            tax, tax_err = self.normalizer.normalize_number(raw_tax, default=0.0, min_val=0.0, max_val=100.0)
            if tax_err:
                errors.append(f"Tax rate: {tax_err}")
            else:
                norm["tax_rate"] = tax

            # Calculated line total
            if norm.get("quantity") and norm.get("unit_price") is not None:
                base_line = norm["quantity"] * norm["unit_price"]
                discount_val = base_line * (norm.get("discount_pct", 0) / 100.0)
                tax_val = (base_line - discount_val) * (norm.get("tax_rate", 0) / 100.0)
                norm["line_total"] = round(base_line - discount_val + tax_val, 2)

            # Sale Date (optional, defaults to today)
            raw_date = row.get(mapping.get("sale_date", ""))
            sdate, date_err = self.normalizer.normalize_date(raw_date, default_today=True)
            if date_err:
                warnings.append(f"Sale date: {date_err}. Using today's date.")
                norm["sale_date"] = str(date.today())
            else:
                norm["sale_date"] = str(sdate)

            # Customer Name
            raw_cust = row.get(mapping.get("customer_name", ""))
            norm["customer_name"] = self.normalizer.clean_str(raw_cust)

            # Notes
            raw_notes = row.get(mapping.get("notes", ""))
            norm["notes"] = self.normalizer.clean_str(raw_notes)

            is_conflict = clean_num and clean_num.upper() in existing_sales
            if errors:
                status = "invalid"
                invalid_count += 1
                action = "error"
            elif warnings:
                status = "warning"
                warning_count += 1
                valid_count += 1
                action = "update" if is_conflict else "create"
            else:
                status = "valid"
                valid_count += 1
                action = "create"

            row_results.append({
                "row_number": idx,
                "status": status,
                "source_data": row,
                "normalized_data": norm,
                "errors": errors,
                "warnings": warnings,
                "is_conflict": bool(is_conflict),
                "action_proposed": action,
            })

        return {
            "valid": invalid_count == 0,
            "total_rows": len(raw_rows),
            "valid_rows": valid_count,
            "warning_rows": warning_count,
            "invalid_rows": invalid_count,
            "duplicate_rows": duplicate_count,
            "row_results": row_results,
        }

    def _validate_inventory(
        self, raw_rows: List[Dict[str, Any]], mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        existing_products = self._get_existing_product_skus()
        existing_warehouses = self._get_existing_warehouses()

        row_results: List[Dict[str, Any]] = []
        valid_count = 0
        warning_count = 0
        invalid_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            errors: List[str] = []
            warnings: List[str] = []
            norm: Dict[str, Any] = {}

            # Product SKU (required)
            raw_sku = row.get(mapping.get("product_sku", ""))
            clean_sku = self.normalizer.clean_str(raw_sku)
            if not clean_sku:
                errors.append("Product SKU is required for inventory adjustment.")
            else:
                norm["product_sku"] = clean_sku
                upper_sku = clean_sku.upper()
                if upper_sku not in existing_products:
                    errors.append(
                        f"Referenced product SKU '{clean_sku}' does not exist in company catalog."
                    )
                else:
                    norm["product_id"] = existing_products[upper_sku]["id"]

            # Warehouse
            raw_wh = row.get(mapping.get("warehouse_name", ""))
            clean_wh = self.normalizer.clean_str(raw_wh)
            if clean_wh:
                upper_wh = clean_wh.upper()
                if upper_wh in existing_warehouses:
                    norm["warehouse_id"] = existing_warehouses[upper_wh]["id"]
                    norm["warehouse_name"] = existing_warehouses[upper_wh]["name"]
                else:
                    # If warehouses exist, require valid warehouse
                    if existing_warehouses:
                        warnings.append(
                            f"Warehouse '{clean_wh}' not found. Will assign to first available warehouse."
                        )
                        first_wh = next(iter(existing_warehouses.values()))
                        norm["warehouse_id"] = first_wh["id"]
                        norm["warehouse_name"] = first_wh["name"]
                    else:
                        errors.append("No active warehouses exist for this company. Please create a warehouse first.")
            else:
                if existing_warehouses:
                    first_wh = next(iter(existing_warehouses.values()))
                    norm["warehouse_id"] = first_wh["id"]
                    norm["warehouse_name"] = first_wh["name"]
                    warnings.append(f"No warehouse specified; using default '{first_wh['name']}'.")
                else:
                    errors.append("No active warehouses exist for this company.")

            # Quantity Delta (required)
            raw_delta = row.get(mapping.get("quantity_delta", ""))
            delta, delta_err = self.normalizer.normalize_number(raw_delta)
            if delta_err:
                errors.append(f"Quantity delta: {delta_err}")
            elif delta is None:
                errors.append("Quantity delta is required (e.g. +10 to add stock, -5 to deduct).")
            elif delta == 0:
                warnings.append("Quantity adjustment is 0; no stock movement will occur.")
                norm["quantity_delta"] = 0.0
            else:
                norm["quantity_delta"] = delta

            # Reorder level (optional)
            raw_reorder = row.get(mapping.get("reorder_level", ""))
            reorder, reorder_err = self.normalizer.normalize_number(raw_reorder, min_val=0.0)
            if reorder_err:
                warnings.append(f"Reorder level: {reorder_err}")
            else:
                norm["reorder_level"] = reorder

            # Notes
            raw_notes = row.get(mapping.get("notes", ""))
            norm["notes"] = self.normalizer.clean_str(raw_notes) or "Batch CSV/Excel stock adjustment"

            if errors:
                status = "invalid"
                invalid_count += 1
                action = "error"
            elif warnings:
                status = "warning"
                warning_count += 1
                valid_count += 1
                action = "adjust"
            else:
                status = "valid"
                valid_count += 1
                action = "adjust"

            row_results.append({
                "row_number": idx,
                "status": status,
                "source_data": row,
                "normalized_data": norm,
                "errors": errors,
                "warnings": warnings,
                "is_conflict": False,
                "action_proposed": action,
            })

        return {
            "valid": invalid_count == 0,
            "total_rows": len(raw_rows),
            "valid_rows": valid_count,
            "warning_rows": warning_count,
            "invalid_rows": invalid_count,
            "duplicate_rows": 0,
            "row_results": row_results,
        }

    def _validate_expenses(
        self, raw_rows: List[Dict[str, Any]], mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        row_results: List[Dict[str, Any]] = []
        valid_count = 0
        warning_count = 0
        invalid_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            errors: List[str] = []
            warnings: List[str] = []
            norm: Dict[str, Any] = {}

            # Description (required)
            raw_desc = row.get(mapping.get("description", ""))
            clean_desc = self.normalizer.clean_str(raw_desc)
            if not clean_desc:
                errors.append("Expense description is required.")
            else:
                norm["description"] = clean_desc

            # Amount (required, > 0)
            raw_amt = row.get(mapping.get("amount", ""))
            amt, amt_err = self.normalizer.normalize_number(raw_amt, min_val=0.01)
            if amt_err:
                errors.append(f"Amount: {amt_err}")
            elif amt is None or amt <= 0:
                errors.append("Expense amount must be greater than 0.")
            else:
                norm["amount"] = amt

            # Expense Date (defaults to today)
            raw_date = row.get(mapping.get("expense_date", ""))
            edate, date_err = self.normalizer.normalize_date(raw_date, default_today=True)
            if date_err:
                warnings.append(f"Expense date: {date_err}. Using today's date.")
                norm["expense_date"] = str(date.today())
            else:
                norm["expense_date"] = str(edate)

            # Category
            raw_cat = row.get(mapping.get("category", ""))
            norm["category"] = self.normalizer.clean_str(raw_cat)

            # Payment Method
            raw_pm = row.get(mapping.get("payment_method", ""))
            pm, pm_err = self.normalizer.normalize_enum(raw_pm, PaymentMethod, default=PaymentMethod.CASH)
            if pm_err:
                warnings.append(f"Payment method: {pm_err}. Defaulted to 'cash'.")
            norm["payment_method"] = pm.value if hasattr(pm, "value") else "cash"

            # Notes
            raw_notes = row.get(mapping.get("notes", ""))
            norm["notes"] = self.normalizer.clean_str(raw_notes)

            if errors:
                status = "invalid"
                invalid_count += 1
                action = "error"
            elif warnings:
                status = "warning"
                warning_count += 1
                valid_count += 1
                action = "create"
            else:
                status = "valid"
                valid_count += 1
                action = "create"

            row_results.append({
                "row_number": idx,
                "status": status,
                "source_data": row,
                "normalized_data": norm,
                "errors": errors,
                "warnings": warnings,
                "is_conflict": False,
                "action_proposed": action,
            })

        return {
            "valid": invalid_count == 0,
            "total_rows": len(raw_rows),
            "valid_rows": valid_count,
            "warning_rows": warning_count,
            "invalid_rows": invalid_count,
            "duplicate_rows": 0,
            "row_results": row_results,
        }

    def _validate_invoices(
        self, raw_rows: List[Dict[str, Any]], mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        existing_invoices = self._get_existing_invoice_numbers()
        file_invs: Set[str] = set()

        row_results: List[Dict[str, Any]] = []
        valid_count = 0
        warning_count = 0
        invalid_count = 0
        duplicate_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            errors: List[str] = []
            warnings: List[str] = []
            norm: Dict[str, Any] = {}

            # Invoice Number (required)
            raw_num = row.get(mapping.get("invoice_number", ""))
            clean_num = self.normalizer.clean_str(raw_num)
            if not clean_num:
                errors.append("Invoice number is required.")
            else:
                norm["invoice_number"] = clean_num
                upper_num = clean_num.upper()
                if upper_num in file_invs:
                    errors.append(f"Duplicate invoice number '{clean_num}' found in upload file.")
                    duplicate_count += 1
                else:
                    file_invs.add(upper_num)

                if upper_num in existing_invoices:
                    warnings.append(
                        f"Invoice '{clean_num}' already exists in database (will skip or update based on policy)."
                    )

            # Invoice Type
            raw_type = row.get(mapping.get("invoice_type", ""))
            itype, itype_err = self.normalizer.normalize_enum(raw_type, InvoiceType, default=InvoiceType.RECEIVABLE)
            if itype_err:
                warnings.append(f"Invoice type: {itype_err}. Defaulted to 'receivable'.")
            norm["invoice_type"] = itype.value if hasattr(itype, "value") else "receivable"

            # Total Amount (required, >= 0)
            raw_total = row.get(mapping.get("total_amount", ""))
            total_amt, total_err = self.normalizer.normalize_number(raw_total, min_val=0.0)
            if total_err:
                errors.append(f"Total amount: {total_err}")
            elif total_amt is None:
                errors.append("Total amount is required.")
            else:
                norm["total_amount"] = total_amt

            # Subtotal (optional)
            raw_sub = row.get(mapping.get("subtotal", ""))
            sub, sub_err = self.normalizer.normalize_number(raw_sub, default=None, min_val=0.0)
            if sub_err:
                errors.append(f"Subtotal: {sub_err}")
            else:
                norm["subtotal"] = sub if sub is not None else norm.get("total_amount", 0.0)

            # Tax Amount (optional)
            raw_tax = row.get(mapping.get("tax_amount", ""))
            tax, tax_err = self.normalizer.normalize_number(raw_tax, default=0.0, min_val=0.0)
            if tax_err:
                errors.append(f"Tax amount: {tax_err}")
            else:
                norm["tax_amount"] = tax

            # Dates
            raw_idate = row.get(mapping.get("invoice_date", ""))
            idate, idate_err = self.normalizer.normalize_date(raw_idate, default_today=True)
            if idate_err:
                warnings.append(f"Invoice date: {idate_err}. Using today's date.")
                norm["invoice_date"] = str(date.today())
            else:
                norm["invoice_date"] = str(idate)

            raw_ddate = row.get(mapping.get("due_date", ""))
            ddate, ddate_err = self.normalizer.normalize_date(raw_ddate, default_today=False)
            norm["due_date"] = str(ddate) if ddate else None

            # Counterparty
            raw_party = row.get(mapping.get("counterparty_name", ""))
            norm["counterparty_name"] = self.normalizer.clean_str(raw_party)

            # Notes
            raw_notes = row.get(mapping.get("notes", ""))
            norm["notes"] = self.normalizer.clean_str(raw_notes)

            is_conflict = clean_num and clean_num.upper() in existing_invoices
            if errors:
                status = "invalid"
                invalid_count += 1
                action = "error"
            elif warnings:
                status = "warning"
                warning_count += 1
                valid_count += 1
                action = "update" if is_conflict else "create"
            else:
                status = "valid"
                valid_count += 1
                action = "create"

            row_results.append({
                "row_number": idx,
                "status": status,
                "source_data": row,
                "normalized_data": norm,
                "errors": errors,
                "warnings": warnings,
                "is_conflict": bool(is_conflict),
                "action_proposed": action,
            })

        return {
            "valid": invalid_count == 0,
            "total_rows": len(raw_rows),
            "valid_rows": valid_count,
            "warning_rows": warning_count,
            "invalid_rows": invalid_count,
            "duplicate_rows": duplicate_count,
            "row_results": row_results,
        }
