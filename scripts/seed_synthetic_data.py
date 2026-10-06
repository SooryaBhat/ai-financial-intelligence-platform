"""
Synthetic ERP Data Seeder & Importer for Supabase
==================================================
Imports existing synthetic ERP datasets from ml/datasets/synthetic/*.csv
into Supabase tables while maintaining full relational integrity,
idempotency (safe re-execution without duplicate errors), and data validation.

Usage:
    python scripts/seed_synthetic_data.py
"""

import os
import sys
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

import pandas as pd
import numpy as np
import dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("seed_synthetic_data")

# ---------------------------------------------------------------------------
# Setup & Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "ml", "datasets", "synthetic")
ENV_PATH = os.path.join(BASE_DIR, ".env")

if not os.path.exists(ENV_PATH):
    # Try parent directory
    ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")

dotenv.load_dotenv(ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing from environment.")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
NAMESPACE_UUID = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def batch_upsert(table_name: str, records: List[Dict[str, Any]], on_conflict: str = None, batch_size: int = 500) -> int:
    """Upsert records into Supabase in batches."""
    if not records:
        logger.info(f"[{table_name}] 0 records to insert.")
        return 0

    inserted_count = 0
    total = len(records)
    
    for i in range(0, total, batch_size):
        chunk = records[i:i + batch_size]
        query = supabase.table(table_name)
        
        # Clean up numpy types / NaN values for JSON serialization
        cleaned_chunk = []
        for row in chunk:
            clean_row = {}
            for k, v in row.items():
                if pd.isna(v) or v is None:
                    clean_row[k] = None
                elif isinstance(v, (np.int64, np.int32, np.int16)):
                    clean_row[k] = int(v)
                elif isinstance(v, (np.float64, np.float32)):
                    clean_row[k] = float(v)
                elif isinstance(v, (np.bool_)):
                    clean_row[k] = bool(v)
                elif isinstance(v, (datetime, date)):
                    clean_row[k] = v.isoformat()
                else:
                    clean_row[k] = v
            cleaned_chunk.append(clean_row)

        try:
            if on_conflict:
                query.upsert(cleaned_chunk, on_conflict=on_conflict).execute()
            else:
                query.upsert(cleaned_chunk).execute()
            inserted_count += len(cleaned_chunk)
            logger.info(f"[{table_name}] Upserted {inserted_count}/{total} records...")
        except Exception as e:
            logger.error(f"Error upserting chunk {i}-{i+batch_size} into {table_name}: {e}")
            raise e

    return inserted_count


def create_auth_user(user_id: str, email: str, name: str) -> None:
    """Ensure user exists in auth.users via Admin API."""
    import urllib.request
    import json
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'id': user_id,
        'email': email,
        'password': 'DemoUserPass123!',
        'email_confirm': True,
        'user_metadata': {'full_name': name}
    }
    
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    
    try:
        with urllib.request.urlopen(req) as resp:
            pass
    except urllib.error.HTTPError as e:
        # If user already exists (422 / 400), that's fine for idempotency
        body = e.read().decode('utf-8')
        if "already been registered" not in body and "already exists" not in body:
            logger.warning(f"Auth user creation notice for {email}: {body}")


# ---------------------------------------------------------------------------
# Import Pipeline
# ---------------------------------------------------------------------------
def run_import():
    logger.info("=== Starting Synthetic ERP Data Import ===")
    logger.info(f"Dataset source: {DATASET_DIR}")
    
    import_results = {}
    
    # -----------------------------------------------------------------------
    # 1. Companies
    # -----------------------------------------------------------------------
    companies_df = pd.read_csv(os.path.join(DATASET_DIR, "companies.csv"))
    companies_records = []
    company_currencies = {}
    
    timezone_map = {
        "India": "Asia/Kolkata",
        "USA": "America/New_York",
        "UAE": "Asia/Dubai"
    }
    
    for _, row in companies_df.iterrows():
        comp_id = row['id']
        name = row['name']
        slug = name.lower().replace(" ", "-").replace(".", "")
        currency = row['currency']
        company_currencies[comp_id] = currency
        
        companies_records.append({
            "id": comp_id,
            "name": name,
            "slug": slug,
            "industry": row['industry'],
            "country": row['country'],
            "currency": currency,
            "timezone": timezone_map.get(row['country'], 'UTC'),
            "is_active": True,
            "created_at": row['created_at']
        })
        
    import_results["companies"] = batch_upsert("companies", companies_records)

    # -----------------------------------------------------------------------
    # 2. Branches
    # -----------------------------------------------------------------------
    branches_df = pd.read_csv(os.path.join(DATASET_DIR, "branches.csv"))
    branches_records = []
    branch_companies = {}
    
    for _, row in branches_df.iterrows():
        b_id = row['id']
        comp_id = row['company_id']
        branch_companies[b_id] = comp_id
        
        branches_records.append({
            "id": b_id,
            "company_id": comp_id,
            "name": row['name'],
            "city": row['city'],
            "is_active": True,
            "created_at": row['created_at']
        })
        
    import_results["branches"] = batch_upsert("branches", branches_records)

    # -----------------------------------------------------------------------
    # 3. Roles Mapping & System Roles Verification
    # -----------------------------------------------------------------------
    roles_res = supabase.table("roles").select("id, name").is_("company_id", "null").execute()
    role_map = {r['name']: r['id'] for r in roles_res.data}
    
    role_name_transform = {
        "admin": "admin",
        "manager": "manager",
        "accountant": "accountant",
        "sales": "sales_rep",
        "owner": "owner",
        "viewer": "viewer"
    }

    # -----------------------------------------------------------------------
    # 4. Users & Company Users
    # -----------------------------------------------------------------------
    users_df = pd.read_csv(os.path.join(DATASET_DIR, "users.csv"))
    public_users_records = []
    company_users_records = []
    user_companies = {}
    
    for _, row in users_df.iterrows():
        u_id = row['id']
        email = row['email']
        name = row['name']
        comp_id = row['company_id']
        user_companies[u_id] = comp_id
        
        # Ensure auth user exists
        create_auth_user(u_id, email, name)
        
        public_users_records.append({
            "id": u_id,
            "email": email,
            "full_name": name,
            "is_active": True,
            "created_at": row['created_at']
        })
        
        csv_role = row['role']
        db_role_name = role_name_transform.get(csv_role, "viewer")
        role_id = role_map.get(db_role_name)
        
        if not role_id:
            logger.warning(f"Role {db_role_name} not found in roles table! Using viewer role.")
            role_id = role_map.get("viewer")
            
        company_users_records.append({
            "company_id": comp_id,
            "user_id": u_id,
            "role_id": role_id,
            "branch_id": row['branch_id'] if pd.notna(row['branch_id']) else None,
            "is_active": True,
            "created_at": row['created_at']
        })
        
    import_results["users"] = batch_upsert("users", public_users_records)
    import_results["company_users"] = batch_upsert("company_users", company_users_records, on_conflict="company_id,user_id")

    # -----------------------------------------------------------------------
    # 5. Customers
    # -----------------------------------------------------------------------
    customers_df = pd.read_csv(os.path.join(DATASET_DIR, "customers.csv"))
    customers_records = []
    customer_companies = {}
    
    for _, row in customers_df.iterrows():
        c_id = row['id']
        comp_id = row['company_id']
        customer_companies[c_id] = comp_id
        
        customers_records.append({
            "id": c_id,
            "company_id": comp_id,
            "name": row['name'],
            "email": row['email'],
            "phone": str(row['phone']) if pd.notna(row['phone']) else None,
            "city": row['city'],
            "credit_limit": float(row['credit_limit']),
            "currency": company_currencies.get(comp_id, "USD"),
            "created_at": row['created_at']
        })
        
    import_results["customers"] = batch_upsert("customers", customers_records)

    # -----------------------------------------------------------------------
    # 6. Suppliers
    # -----------------------------------------------------------------------
    suppliers_df = pd.read_csv(os.path.join(DATASET_DIR, "suppliers.csv"))
    suppliers_records = []
    supplier_companies = {}
    
    for _, row in suppliers_df.iterrows():
        s_id = row['id']
        comp_id = row['company_id']
        supplier_companies[s_id] = comp_id
        
        suppliers_records.append({
            "id": s_id,
            "company_id": comp_id,
            "name": row['name'],
            "email": row['contact_email'],
            "phone": str(row['phone']) if pd.notna(row['phone']) else None,
            "city": row['city'],
            "payment_terms_days": int(row['payment_terms_days']),
            "currency": company_currencies.get(comp_id, "USD"),
            "created_at": row['created_at']
        })
        
    import_results["suppliers"] = batch_upsert("suppliers", suppliers_records)

    # -----------------------------------------------------------------------
    # 7. Categories (Product Categories + Expense Categories)
    # -----------------------------------------------------------------------
    categories_df = pd.read_csv(os.path.join(DATASET_DIR, "categories.csv"))
    categories_records = []
    
    for _, row in categories_df.iterrows():
        categories_records.append({
            "id": row['id'],
            "company_id": row['company_id'],
            "name": row['name'],
            "type": "product",
            "description": row['description'],
            "created_at": row['created_at']
        })
        
    # Also extract expense categories from expenses.csv
    expenses_df = pd.read_csv(os.path.join(DATASET_DIR, "expenses.csv"))
    expense_category_map = {} # (comp_id, cat_name) -> category_id
    
    distinct_exp_cats = expenses_df[['company_id', 'category']].drop_duplicates()
    for _, row in distinct_exp_cats.iterrows():
        comp_id = row['company_id']
        cat_name = row['category']
        cat_id = str(uuid.uuid5(NAMESPACE_UUID, f"exp_cat:{comp_id}:{cat_name}"))
        expense_category_map[(comp_id, cat_name)] = cat_id
        
        categories_records.append({
            "id": cat_id,
            "company_id": comp_id,
            "name": cat_name,
            "type": "expense",
            "description": f"{cat_name} expense category",
            "created_at": "2021-06-01T09:00:00"
        })
        
    import_results["categories"] = batch_upsert("categories", categories_records)

    # -----------------------------------------------------------------------
    # 8. Products
    # -----------------------------------------------------------------------
    products_df = pd.read_csv(os.path.join(DATASET_DIR, "products.csv"))
    products_records = []
    product_companies = {}
    
    for _, row in products_df.iterrows():
        p_id = row['id']
        comp_id = row['company_id']
        product_companies[p_id] = comp_id
        
        products_records.append({
            "id": p_id,
            "company_id": comp_id,
            "category_id": row['category_id'],
            "name": row['name'],
            "sku": row['sku'],
            "unit": row['unit'],
            "cost_price": float(row['cost_price']),
            "selling_price": float(row['selling_price']),
            "tax_rate": 0.0,
            "type": "product",
            "is_active": bool(row['is_active']),
            "created_at": row['created_at']
        })
        
    import_results["products"] = batch_upsert("products", products_records)

    # -----------------------------------------------------------------------
    # 9. Warehouses
    # -----------------------------------------------------------------------
    warehouses_df = pd.read_csv(os.path.join(DATASET_DIR, "warehouses.csv"))
    warehouses_records = []
    branch_primary_warehouse = {} # branch_id -> warehouse_id
    
    for _, row in warehouses_df.iterrows():
        w_id = row['id']
        b_id = row['branch_id']
        if b_id not in branch_primary_warehouse:
            branch_primary_warehouse[b_id] = w_id
            
        warehouses_records.append({
            "id": w_id,
            "company_id": row['company_id'],
            "branch_id": b_id,
            "name": row['name'],
            "address": row['location'],
            "is_active": True,
            "created_at": row['created_at']
        })
        
    import_results["warehouses"] = batch_upsert("warehouses", warehouses_records)

    # -----------------------------------------------------------------------
    # 10. Inventory
    # -----------------------------------------------------------------------
    inventory_df = pd.read_csv(os.path.join(DATASET_DIR, "inventory.csv"))
    inventory_records = []
    
    for _, row in inventory_df.iterrows():
        p_id = row['product_id']
        comp_id = product_companies.get(p_id)
        
        inventory_records.append({
            "id": row['id'],
            "company_id": comp_id,
            "product_id": p_id,
            "warehouse_id": row['warehouse_id'],
            "quantity": float(row['quantity_on_hand']),
            "reorder_level": float(row['reorder_level']),
            "updated_at": row['updated_at']
        })
        
    import_results["inventory"] = batch_upsert("inventory", inventory_records, on_conflict="product_id,warehouse_id")

    # -----------------------------------------------------------------------
    # 11. Sales
    # -----------------------------------------------------------------------
    sales_df = pd.read_csv(os.path.join(DATASET_DIR, "sales.csv"))
    sales_records = []
    sale_branches = {}
    sale_companies = {}
    
    sale_status_map = {
        "completed": "delivered",
        "pending": "draft",
        "cancelled": "cancelled"
    }
    
    for _, row in sales_df.iterrows():
        s_id = row['id']
        comp_id = row['company_id']
        b_id = row['branch_id']
        sale_branches[s_id] = b_id
        sale_companies[s_id] = comp_id
        
        status_val = sale_status_map.get(row['status'], "draft")
        sale_num = f"SL-{s_id[:8].upper()}"
        
        sales_records.append({
            "id": s_id,
            "company_id": comp_id,
            "branch_id": b_id,
            "customer_id": row['customer_id'],
            "sale_number": sale_num,
            "sale_date": row['sale_date'],
            "status": status_val,
            "subtotal": float(row['total_amount']),
            "discount_amount": float(row['discount_amount']),
            "tax_amount": float(row['tax_amount']),
            "total_amount": float(row['net_amount']),
            "currency": company_currencies.get(comp_id, "USD"),
            "created_by": row['user_id'],
            "created_at": row['created_at']
        })
        
    import_results["sales"] = batch_upsert("sales", sales_records)

    # -----------------------------------------------------------------------
    # 12. Sale Items
    # -----------------------------------------------------------------------
    sale_items_df = pd.read_csv(os.path.join(DATASET_DIR, "sale_items.csv"))
    sale_items_records = []
    
    for _, row in sale_items_df.iterrows():
        s_id = row['sale_id']
        b_id = sale_branches.get(s_id)
        w_id = branch_primary_warehouse.get(b_id)
        
        sale_items_records.append({
            "id": row['id'],
            "sale_id": s_id,
            "product_id": row['product_id'],
            "warehouse_id": w_id,
            "quantity": float(row['quantity']),
            "unit_price": float(row['unit_price']),
            "discount_pct": float(row['discount_pct']),
            "tax_rate": 0.0,
            "line_total": float(row['line_total'])
        })
        
    import_results["sale_items"] = batch_upsert("sale_items", sale_items_records)

    # -----------------------------------------------------------------------
    # 13. Purchases
    # -----------------------------------------------------------------------
    purchases_df = pd.read_csv(os.path.join(DATASET_DIR, "purchases.csv"))
    purchases_records = []
    purchase_branches = {}
    purchase_companies = {}
    purchase_statuses = {}
    
    pur_status_map = {
        "received": "received",
        "pending": "draft",
        "cancelled": "cancelled"
    }
    
    for _, row in purchases_df.iterrows():
        pur_id = row['id']
        comp_id = row['company_id']
        b_id = row['branch_id']
        status_val = pur_status_map.get(row['status'], "draft")
        
        purchase_branches[pur_id] = b_id
        purchase_companies[pur_id] = comp_id
        purchase_statuses[pur_id] = status_val
        
        po_num = f"PO-{pur_id[:8].upper()}"
        
        purchases_records.append({
            "id": pur_id,
            "company_id": comp_id,
            "branch_id": b_id,
            "supplier_id": row['supplier_id'],
            "purchase_number": po_num,
            "purchase_date": row['purchase_date'],
            "status": status_val,
            "subtotal": float(row['total_amount']),
            "tax_amount": float(row['tax_amount']),
            "total_amount": float(row['net_amount']),
            "currency": company_currencies.get(comp_id, "USD"),
            "created_by": row['user_id'],
            "created_at": row['created_at']
        })
        
    import_results["purchases"] = batch_upsert("purchases", purchases_records)

    # -----------------------------------------------------------------------
    # 14. Purchase Items
    # -----------------------------------------------------------------------
    purchase_items_df = pd.read_csv(os.path.join(DATASET_DIR, "purchase_items.csv"))
    purchase_items_records = []
    
    for _, row in purchase_items_df.iterrows():
        pur_id = row['purchase_id']
        b_id = purchase_branches.get(pur_id)
        w_id = branch_primary_warehouse.get(b_id)
        pur_status = purchase_statuses.get(pur_id, "draft")
        qty = float(row['quantity'])
        
        purchase_items_records.append({
            "id": row['id'],
            "purchase_id": pur_id,
            "product_id": row['product_id'],
            "warehouse_id": w_id,
            "quantity": qty,
            "unit_cost": float(row['unit_cost']),
            "tax_rate": 0.0,
            "line_total": float(row['line_total']),
            "received_qty": qty if pur_status == "received" else 0.0
        })
        
    import_results["purchase_items"] = batch_upsert("purchase_items", purchase_items_records)

    # -----------------------------------------------------------------------
    # 15. Invoices (AR Invoices for Sales + AP Invoices for Purchases)
    # -----------------------------------------------------------------------
    invoices_df = pd.read_csv(os.path.join(DATASET_DIR, "invoices.csv"))
    invoices_records = []
    sale_invoice_map = {} # sale_id -> invoice_id
    purchase_invoice_map = {} # purchase_id -> invoice_id
    
    # 15a. Receivable Invoices from invoices.csv (Sales)
    for _, row in invoices_df.iterrows():
        inv_id = row['id']
        s_id = row['sale_id']
        comp_id = row['company_id']
        sale_invoice_map[s_id] = inv_id
        
        invoices_records.append({
            "id": inv_id,
            "company_id": comp_id,
            "invoice_type": "receivable",
            "invoice_number": row['invoice_number'],
            "invoice_date": row['invoice_date'],
            "due_date": row['due_date'],
            "customer_id": row['customer_id'],
            "sale_id": s_id,
            "status": row['status'],
            "subtotal": float(row['total_amount']),
            "tax_amount": 0.0,
            "total_amount": float(row['total_amount']),
            "amount_paid": float(row['paid_amount']),
            "currency": company_currencies.get(comp_id, "USD"),
            "created_at": row['created_at']
        })
        
    # 15b. Payable Invoices for Purchases (AP)
    for _, row in purchases_df.iterrows():
        pur_id = row['id']
        comp_id = row['company_id']
        ap_inv_id = str(uuid.uuid5(NAMESPACE_UUID, f"pur_inv:{pur_id}"))
        purchase_invoice_map[pur_id] = ap_inv_id
        
        p_status = row['payment_status']
        inv_status = "paid" if p_status == "paid" else "partial" if p_status == "partial" else "sent"
        paid_amt = float(row['net_amount']) if p_status == "paid" else 0.0
        
        invoices_records.append({
            "id": ap_inv_id,
            "company_id": comp_id,
            "invoice_type": "payable",
            "invoice_number": f"PINV-{pur_id[:8].upper()}",
            "invoice_date": row['purchase_date'],
            "due_date": row['purchase_date'],
            "supplier_id": row['supplier_id'],
            "purchase_id": pur_id,
            "status": inv_status,
            "subtotal": float(row['total_amount']),
            "tax_amount": float(row['tax_amount']),
            "total_amount": float(row['net_amount']),
            "amount_paid": paid_amt,
            "currency": company_currencies.get(comp_id, "USD"),
            "created_at": row['created_at']
        })
        
    import_results["invoices"] = batch_upsert("invoices", invoices_records)

    # -----------------------------------------------------------------------
    # 16. Payments
    # -----------------------------------------------------------------------
    payments_df = pd.read_csv(os.path.join(DATASET_DIR, "payments.csv"))
    payments_records = []
    
    for _, row in payments_df.iterrows():
        ref_type = row['reference_type']
        ref_id = row['reference_id']
        comp_id = row['company_id']
        
        inv_id = None
        if ref_type == "sale":
            inv_id = sale_invoice_map.get(ref_id)
        elif ref_type == "purchase":
            inv_id = purchase_invoice_map.get(ref_id)
            
        if not inv_id:
            logger.warning(f"Payment {row['id']} has no matching invoice for {ref_type} {ref_id}")
            continue
            
        pay_id = row['id']
        payments_records.append({
            "id": pay_id,
            "company_id": comp_id,
            "invoice_id": inv_id,
            "payment_date": row['payment_date'],
            "amount": float(row['amount']),
            "payment_method": row['payment_method'],
            "reference": f"PAY-{pay_id[:8].upper()}",
            "currency": company_currencies.get(comp_id, "USD"),
            "exchange_rate": 1.0,
            "created_at": row['created_at']
        })
        
    import_results["payments"] = batch_upsert("payments", payments_records)

    # -----------------------------------------------------------------------
    # 17. Stock Movements
    # -----------------------------------------------------------------------
    sm_df = pd.read_csv(os.path.join(DATASET_DIR, "stock_movements.csv"))
    sm_records = []
    
    for _, row in sm_df.iterrows():
        p_id = row['product_id']
        comp_id = product_companies.get(p_id)
        reason_val = str(row['reason']) if pd.notna(row['reason']) else "manual"
        mv_type_csv = str(row['movement_type'])
        qty = float(row['quantity'])
        
        # Determine movement_type & reference_type according to Supabase DB constraints
        if reason_val == "sale":
            db_mv_type = "sale"
            ref_type = "sale"
            final_qty = -abs(qty)
        elif reason_val == "purchase":
            db_mv_type = "receipt"
            ref_type = "purchase"
            final_qty = abs(qty)
        elif reason_val == "return":
            db_mv_type = "return"
            ref_type = "manual"
            final_qty = abs(qty) if mv_type_csv == "in" else -abs(qty)
        elif reason_val == "transfer":
            db_mv_type = "transfer_in" if mv_type_csv == "in" else "transfer_out"
            ref_type = "manual"
            final_qty = abs(qty) if mv_type_csv == "in" else -abs(qty)
        else: # adjustment, write_off, etc.
            db_mv_type = "adjustment"
            ref_type = "manual"
            final_qty = abs(qty) if mv_type_csv == "in" else -abs(qty)

        ref_id = row['reference_id'] if pd.notna(row['reference_id']) else None

        sm_records.append({
            "id": row['id'],
            "company_id": comp_id,
            "product_id": p_id,
            "warehouse_id": row['warehouse_id'],
            "movement_type": db_mv_type,
            "quantity": final_qty,
            "reference_type": ref_type,
            "reference_id": ref_id,
            "created_at": row['moved_at']
        })
        
    import_results["stock_movements"] = batch_upsert("stock_movements", sm_records)

    # -----------------------------------------------------------------------
    # 18. Expenses
    # -----------------------------------------------------------------------
    expenses_records = []
    
    for _, row in expenses_df.iterrows():
        comp_id = row['company_id']
        cat_name = row['category']
        cat_id = expense_category_map.get((comp_id, cat_name))
        
        expenses_records.append({
            "id": row['id'],
            "company_id": comp_id,
            "branch_id": row['branch_id'],
            "category_id": cat_id,
            "description": row['description'],
            "amount": float(row['amount']),
            "expense_date": row['expense_date'],
            "status": row['status'],
            "created_by": row['user_id'],
            "created_at": row['created_at']
        })
        
    import_results["expenses"] = batch_upsert("expenses", expenses_records)

    logger.info("=== IMPORT COMPLETED SUCCESSFULLY ===")
    return import_results


# ---------------------------------------------------------------------------
# Validation Pipeline
# ---------------------------------------------------------------------------
def run_validation():
    logger.info("\n=== Starting Post-Import Data Validation ===")
    validation = {}
    
    tables_to_check = [
        "companies", "branches", "users", "company_users", "customers",
        "suppliers", "categories", "products", "warehouses", "inventory",
        "sales", "sale_items", "purchases", "purchase_items", "invoices",
        "payments", "stock_movements", "expenses"
    ]
    
    row_counts = {}
    for table in tables_to_check:
        res = supabase.table(table).select("id", count="exact").execute()
        row_counts[table] = res.count if res.count is not None else len(res.data)
        
    validation["row_counts"] = row_counts
    logger.info(f"Row counts per table: {row_counts}")

    # Verify foreign key relationships and integrity
    main_company_id = "00000000-0000-0000-0000-000000000001"
    comp_res = supabase.table("companies").select("*").eq("id", main_company_id).execute()
    validation["main_company_exists"] = len(comp_res.data) == 1
    if len(comp_res.data) == 1:
        logger.info(f"Main Demo Company Verified: {comp_res.data[0]['name']} ({main_company_id})")

    # Validate sales -> sale_items link
    sales_sample = supabase.table("sales").select("id").limit(5).execute()
    sample_sale_ids = [s['id'] for s in sales_sample.data]
    items_count = supabase.table("sale_items").select("id", count="exact").in_("sale_id", sample_sale_ids).execute()
    validation["sales_has_items"] = items_count.count > 0
    logger.info(f"Verified sales -> sale_items relationship: sample sale IDs have {items_count.count} items.")

    # Validate purchases -> purchase_items link
    pur_sample = supabase.table("purchases").select("id").limit(5).execute()
    sample_pur_ids = [p['id'] for p in pur_sample.data]
    pur_items_count = supabase.table("purchase_items").select("id", count="exact").in_("purchase_id", sample_pur_ids).execute()
    validation["purchases_has_items"] = pur_items_count.count > 0
    logger.info(f"Verified purchases -> purchase_items relationship: sample purchase IDs have {pur_items_count.count} items.")

    # Validate invoices -> payments link
    pay_sample = supabase.table("payments").select("invoice_id").limit(10).execute()
    inv_ids = list(set([p['invoice_id'] for p in pay_sample.data if p.get('invoice_id')]))
    inv_check = supabase.table("invoices").select("id").in_("id", inv_ids).execute()
    validation["payments_linked_to_invoices"] = len(inv_check.data) == len(inv_ids)
    logger.info(f"Verified payments -> invoices relationship: all {len(inv_ids)} sample payments match valid invoices.")

    return validation

if __name__ == "__main__":
    import_results = run_import()
    validation_results = run_validation()
    print("\nSUMMARY_JSON:" + str({
        "import_results": import_results,
        "validation_results": validation_results
    }))
