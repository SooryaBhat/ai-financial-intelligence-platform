"""
Import normalizer service.
Provides destination entity schemas, fuzzy column mapping suggestion logic,
and type-safe value normalization for dates, numbers, enums, and currencies.
"""
from datetime import date, datetime
import re
from typing import Any, Dict, List, Optional, Tuple, Type
from dateutil import parser as date_parser

from app.core.constants import (
    ExpenseStatus,
    InvoiceStatus,
    InvoiceType,
    PaymentMethod,
    ProductType,
    SaleStatus,
)


ENTITY_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "products": {
        "title": "Products",
        "description": "Product catalog records with SKUs, pricing, and category assignments",
        "fields": [
            {
                "name": "name",
                "label": "Product Name",
                "required": True,
                "type": "string",
                "description": "Unique product display name",
                "aliases": ["product", "product_name", "item_name", "name", "title", "description_short"],
            },
            {
                "name": "sku",
                "label": "SKU / Code",
                "required": False,
                "type": "string",
                "description": "Stock Keeping Unit or barcode",
                "aliases": ["sku", "item_code", "product_code", "code", "barcode", "part_number"],
            },
            {
                "name": "selling_price",
                "label": "Selling Price",
                "required": True,
                "type": "number",
                "description": "Default customer unit selling price",
                "aliases": ["selling_price", "price", "unit_price", "rate", "mrp", "retail_price", "sales_price"],
            },
            {
                "name": "cost_price",
                "label": "Cost Price",
                "required": False,
                "type": "number",
                "description": "Cost or procurement price per unit",
                "aliases": ["cost_price", "cost", "purchase_price", "buying_price", "buying_cost", "purchase_cost", "unit_cost"],
            },
            {
                "name": "tax_rate",
                "label": "Tax Rate (%)",
                "required": False,
                "type": "number",
                "description": "Applicable tax percentage (0 to 100)",
                "aliases": ["tax_rate", "tax_pct", "tax", "gst", "vat", "gst_rate"],
            },
            {
                "name": "category",
                "label": "Category Name",
                "required": False,
                "type": "string",
                "description": "Product category reference",
                "aliases": ["category", "category_name", "group", "product_category", "department", "dept"],
            },
            {
                "name": "unit",
                "label": "Unit of Measurement",
                "required": False,
                "type": "string",
                "description": "Unit (e.g. pcs, kg, box, ltr)",
                "aliases": ["unit", "uom", "unit_of_measure", "units"],
            },
            {
                "name": "type",
                "label": "Type",
                "required": False,
                "type": "enum",
                "options": ["product", "service"],
                "description": "'product' for physical goods, 'service' for non-inventory services",
                "aliases": ["type", "product_type", "item_type"],
            },
            {
                "name": "description",
                "label": "Description",
                "required": False,
                "type": "string",
                "description": "Full product description or specifications",
                "aliases": ["description", "details", "specifications", "notes"],
            },
        ],
    },
    "sales": {
        "title": "Sales Orders & Line Items",
        "description": "Sales orders with product line items, quantities, and prices",
        "fields": [
            {
                "name": "sale_number",
                "label": "Sale / Order Number",
                "required": True,
                "type": "string",
                "description": "Unique sales order reference code",
                "aliases": ["sale_number", "order_number", "order_id", "sale_id", "invoice_number", "bill_no", "order_no"],
            },
            {
                "name": "sale_date",
                "label": "Sale Date",
                "required": False,
                "type": "date",
                "description": "Date order was placed (defaults to today)",
                "aliases": ["sale_date", "date", "order_date", "invoice_date", "transaction_date"],
            },
            {
                "name": "customer_name",
                "label": "Customer Name",
                "required": False,
                "type": "string",
                "description": "Customer name or walk-in buyer",
                "aliases": ["customer", "customer_name", "client", "buyer", "customer_ref"],
            },
            {
                "name": "product_sku",
                "label": "Product SKU / Code",
                "required": True,
                "type": "string",
                "description": "SKU or code of the sold product",
                "aliases": ["product_sku", "sku", "item_code", "product_code", "product"],
            },
            {
                "name": "quantity",
                "label": "Quantity",
                "required": True,
                "type": "number",
                "description": "Quantity sold (positive numeric value)",
                "aliases": ["quantity", "qty", "count", "units", "quantity_sold"],
            },
            {
                "name": "unit_price",
                "label": "Unit Price",
                "required": True,
                "type": "number",
                "description": "Selling price per item unit",
                "aliases": ["unit_price", "price", "rate", "selling_price"],
            },
            {
                "name": "discount_pct",
                "label": "Discount (%)",
                "required": False,
                "type": "number",
                "description": "Line discount percentage (0 to 100)",
                "aliases": ["discount_pct", "discount", "disc_pct", "discount_percentage"],
            },
            {
                "name": "tax_rate",
                "label": "Tax Rate (%)",
                "required": False,
                "type": "number",
                "description": "Tax percentage applied to line item",
                "aliases": ["tax_rate", "tax_pct", "tax", "gst", "vat"],
            },
            {
                "name": "notes",
                "label": "Notes / Memo",
                "required": False,
                "type": "string",
                "description": "Optional order notes or customer remarks",
                "aliases": ["notes", "memo", "remarks", "comments"],
            },
        ],
    },
    "inventory": {
        "title": "Inventory Adjustments & Stock Balances",
        "description": "Product stock quantity adjustments and reorder level synchronization",
        "fields": [
            {
                "name": "product_sku",
                "label": "Product SKU / Code",
                "required": True,
                "type": "string",
                "description": "SKU of product to adjust",
                "aliases": ["product_sku", "sku", "item_code", "product_code", "product"],
            },
            {
                "name": "warehouse_name",
                "label": "Warehouse",
                "required": False,
                "type": "string",
                "description": "Target warehouse name or ID",
                "aliases": ["warehouse", "warehouse_name", "location", "store", "outlet", "godown"],
            },
            {
                "name": "quantity_delta",
                "label": "Quantity Delta (+ / -)",
                "required": True,
                "type": "number",
                "description": "Stock adjustment quantity (positive to add, negative to deduct)",
                "aliases": ["quantity_delta", "delta", "adjustment", "qty_change", "quantity_change", "count_delta", "quantity", "qty"],
            },
            {
                "name": "reorder_level",
                "label": "Reorder Level",
                "required": False,
                "type": "number",
                "description": "Minimum stock threshold triggering reorder alerts",
                "aliases": ["reorder_level", "min_stock", "reorder_point", "safety_stock"],
            },
            {
                "name": "notes",
                "label": "Reason / Notes",
                "required": False,
                "type": "string",
                "description": "Audit adjustment notes (e.g. physical count, breakage, replenishment)",
                "aliases": ["notes", "reason", "memo", "remarks", "reference"],
            },
        ],
    },
    "expenses": {
        "title": "Operating Expenses",
        "description": "Expense vouchers, receipts, and vendor payments",
        "fields": [
            {
                "name": "description",
                "label": "Expense Description",
                "required": True,
                "type": "string",
                "description": "Description of the business expenditure",
                "aliases": ["description", "expense_name", "item", "title", "particulars", "memo"],
            },
            {
                "name": "amount",
                "label": "Amount",
                "required": True,
                "type": "number",
                "description": "Total expense amount (positive numeric value)",
                "aliases": ["amount", "total", "expense_amount", "cost", "total_amount", "paid_amount"],
            },
            {
                "name": "expense_date",
                "label": "Expense Date",
                "required": False,
                "type": "date",
                "description": "Date expense was incurred (defaults to today)",
                "aliases": ["expense_date", "date", "transaction_date", "bill_date", "payment_date"],
            },
            {
                "name": "category",
                "label": "Expense Category",
                "required": False,
                "type": "string",
                "description": "Category (e.g. Utilities, Rent, Office Supplies, Travel)",
                "aliases": ["category", "expense_category", "type", "head", "account"],
            },
            {
                "name": "payment_method",
                "label": "Payment Method",
                "required": False,
                "type": "enum",
                "options": ["cash", "bank_transfer", "card", "cheque", "other"],
                "description": "Payment mode used",
                "aliases": ["payment_method", "payment_mode", "mode", "payment_type"],
            },
            {
                "name": "notes",
                "label": "Notes / Receipt Ref",
                "required": False,
                "type": "string",
                "description": "Reference voucher number or notes",
                "aliases": ["notes", "receipt_ref", "voucher_no", "reference"],
            },
        ],
    },
    "invoices": {
        "title": "Invoices (Receivable & Payable)",
        "description": "Official invoices for customer receivables or vendor payables",
        "fields": [
            {
                "name": "invoice_number",
                "label": "Invoice Number",
                "required": True,
                "type": "string",
                "description": "Unique tax invoice identifier",
                "aliases": ["invoice_number", "invoice_no", "inv_num", "bill_number", "bill_no", "invoice_id"],
            },
            {
                "name": "invoice_type",
                "label": "Invoice Type",
                "required": False,
                "type": "enum",
                "options": ["receivable", "payable"],
                "description": "'receivable' for customer invoices, 'payable' for vendor bills (default: receivable)",
                "aliases": ["invoice_type", "type", "direction", "category"],
            },
            {
                "name": "invoice_date",
                "label": "Invoice Date",
                "required": False,
                "type": "date",
                "description": "Invoice issue date",
                "aliases": ["invoice_date", "date", "issue_date", "bill_date"],
            },
            {
                "name": "due_date",
                "label": "Due Date",
                "required": False,
                "type": "date",
                "description": "Payment due date",
                "aliases": ["due_date", "payment_due", "terms_date"],
            },
            {
                "name": "counterparty_name",
                "label": "Customer / Supplier Name",
                "required": False,
                "type": "string",
                "description": "Customer name (receivable) or Supplier name (payable)",
                "aliases": ["customer_name", "supplier_name", "client", "vendor", "party_name", "counterparty"],
            },
            {
                "name": "subtotal",
                "label": "Subtotal (Before Tax)",
                "required": False,
                "type": "number",
                "description": "Net amount before taxes",
                "aliases": ["subtotal", "taxable_amount", "net_amount", "base_amount"],
            },
            {
                "name": "tax_amount",
                "label": "Tax Amount",
                "required": False,
                "type": "number",
                "description": "Total tax or GST amount",
                "aliases": ["tax_amount", "tax", "gst_amount", "vat_amount"],
            },
            {
                "name": "total_amount",
                "label": "Total Amount",
                "required": True,
                "type": "number",
                "description": "Final invoice total including tax",
                "aliases": ["total_amount", "total", "grand_total", "invoice_total", "amount"],
            },
            {
                "name": "notes",
                "label": "Notes / Terms",
                "required": False,
                "type": "string",
                "description": "Payment terms or remarks",
                "aliases": ["notes", "terms", "remarks"],
            },
        ],
    },
}


class ImportNormalizer:
    @staticmethod
    def get_entity_schema(entity_type: str) -> Dict[str, Any]:
        """Retrieve entity mapping schema definition."""
        schema = ENTITY_SCHEMAS.get(entity_type)
        if not schema:
            raise ValueError(f"Unknown entity type: '{entity_type}'. Supported: {list(ENTITY_SCHEMAS.keys())}")
        return schema

    @classmethod
    def suggest_mappings(cls, entity_type: str, source_headers: List[str]) -> Dict[str, str]:
        """
        Suggest mapping from source_headers to destination fields using fuzzy alias matching.
        Returns dict of { source_header: destination_field_name }
        """
        schema = cls.get_entity_schema(entity_type)
        fields = schema["fields"]
        suggestions: Dict[str, str] = {}
        assigned_dest_fields = set()

        def clean_token(s: str) -> str:
            return re.sub(r"[^a-z0-9]", "", s.lower())

        for header in source_headers:
            clean_hdr = clean_token(header)
            best_match: Optional[str] = None

            for field in fields:
                dest_name = field["name"]
                if dest_name in assigned_dest_fields:
                    continue

                # Check exact field name
                if clean_hdr == clean_token(dest_name):
                    best_match = dest_name
                    break

                # Check label
                if clean_hdr == clean_token(field["label"]):
                    best_match = dest_name
                    break

                # Check aliases
                for alias in field.get("aliases", []):
                    if clean_hdr == clean_token(alias):
                        best_match = dest_name
                        break
                if best_match:
                    break

            if best_match:
                suggestions[header] = best_match
                assigned_dest_fields.add(best_match)

        return suggestions

    @staticmethod
    def clean_str(val: Any) -> Optional[str]:
        """Convert value to stripped string or None if empty."""
        if val is None:
            return None
        s = str(val).strip()
        if s.startswith("'"):
            # Remove leading quote if it was added for spreadsheet injection defense
            s = s[1:].strip()
        return s if s else None

    @staticmethod
    def normalize_number(
        val: Any,
        default: Optional[float] = None,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Clean currency symbols, commas, spaces and parse to float.
        Returns (parsed_value, error_message).
        """
        if val is None or val == "":
            return default, None

        if isinstance(val, (int, float)):
            num = float(val)
        else:
            s = str(val).strip()
            if s.startswith("'"):
                s = s[1:].strip()
            # Remove currency signs and commas: $, ₹, €, £, comma
            s_clean = re.sub(r"[\$₹€£,\s]", "", s)
            if not s_clean:
                return default, None
            try:
                num = float(s_clean)
            except ValueError:
                return None, f"Invalid numeric value: '{val}'"

        if min_val is not None and num < min_val:
            return None, f"Value {num} is below minimum allowed ({min_val})"
        if max_val is not None and num > max_val:
            return None, f"Value {num} exceeds maximum allowed ({max_val})"

        return num, None

    @staticmethod
    def normalize_date(val: Any, default_today: bool = False) -> Tuple[Optional[date], Optional[str]]:
        """Parse various date formats into date object."""
        if val is None or val == "":
            return (date.today(), None) if default_today else (None, None)

        if isinstance(val, date) and not isinstance(val, datetime):
            return val, None
        if isinstance(val, datetime):
            return val.date(), None

        s = str(val).strip()
        if s.startswith("'"):
            s = s[1:].strip()

        try:
            # Handle common Indian/UK DD/MM/YYYY or US MM/DD/YYYY formats
            parsed = date_parser.parse(s, dayfirst=True)
            return parsed.date(), None
        except Exception:
            try:
                parsed = date_parser.parse(s, dayfirst=False)
                return parsed.date(), None
            except Exception:
                return None, f"Unable to parse date: '{val}'. Expected format YYYY-MM-DD or DD/MM/YYYY"

    @staticmethod
    def normalize_enum(val: Any, enum_cls: Type[Any], default: Any = None) -> Tuple[Any, Optional[str]]:
        """Normalize case-insensitive enum value."""
        if val is None or val == "":
            return default, None

        s = str(val).strip().lower()
        if s.startswith("'"):
            s = s[1:].strip().lower()

        # Match enum value or name
        for item in enum_cls:
            if s == item.value.lower() or s == item.name.lower():
                return item, None

        valid_vals = [e.value for e in enum_cls]
        return None, f"Invalid value '{val}'. Allowed options: {', '.join(valid_vals)}"

    @staticmethod
    def normalize_bool(val: Any, default: bool = True) -> bool:
        """Parse boolean values from strings like 'true', 'yes', '1', 'active'."""
        if val is None or val == "":
            return default
        s = str(val).strip().lower()
        if s in ("true", "1", "yes", "y", "active", "enabled"):
            return True
        if s in ("false", "0", "no", "n", "inactive", "disabled"):
            return False
        return default
