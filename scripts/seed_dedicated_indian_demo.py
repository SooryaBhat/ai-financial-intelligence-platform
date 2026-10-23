# -*- coding: utf-8 -*-
"""
seed_dedicated_indian_demo.py
==============================
Creates and populates the dedicated Indian demo company:
- Company ID: 11111111-0000-0000-0000-000000000001
- Company Name: ALLADIN India Demo Retail
- Country: India | Currency: INR (₹) | Timezone: Asia/Kolkata
- Branches: Mangaluru Central HQ, Bengaluru Flagship, Mysuru Depot
- Warehouses: Mangaluru Central, Mangaluru Reserve, Bengaluru Hub, Mysuru Depot
- Demo Account: demo.india@alladin.ai / DemoUserPass123!
- Complete 2022 to 2026 current-year (Oct 21, 2026) Indian retail transactional data.
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd

# Add backend to path
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.append(BACKEND_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.database.client import get_admin_client, get_anon_client

DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "datasets", "synthetic")

DEMO_COMPANY_ID = "11111111-0000-0000-0000-000000000001"
SOURCE_COMPANY_ID = "00000000-0000-0000-0000-000000000001"

DEMO_USER_EMAIL = "demo.india@alladin.ai"
DEMO_USER_PASS = "DemoUserPass123!"
DEMO_USER_NAME = "Demo Manager India"

# Deterministic namespace for demo UUID mapping
DEMO_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "alladin.india.retail.2026")

def map_uuid(entity_type: str, old_id: str) -> str:
    if not old_id or pd.isna(old_id):
        return None
    return str(uuid.uuid5(DEMO_NAMESPACE, f"{entity_type}_{old_id}"))

# Branch mappings (Mumbai -> Mangaluru, Pune -> Bengaluru, Ahmedabad -> Mysuru)
BRANCH_MAP = {
    "bdd640fb-0667-4ad1-9c80-317fa3b1799d": "11111111-0001-0000-0000-000000000001", # Mangaluru
    "23b8c1e9-3924-46de-beb1-3b9046685257": "11111111-0001-0000-0000-000000000002", # Bengaluru
    "bd9c66b3-ad3c-4d6d-9a3d-1fa7bc8960a9": "11111111-0001-0000-0000-000000000003", # Mysuru
}

# Warehouse mappings
WAREHOUSE_MAP = {
    "ea98fef8-d0d7-4e37-bbf2-025f4a0d2b73": "11111111-0002-0000-0000-000000000001", # Mangaluru Central
    "93d563ae-51a3-4c26-937b-f79bbb44badc": "11111111-0002-0000-0000-000000000002", # Mangaluru Reserve
    "d18183d1-ac2b-4cfc-85c5-1060991121e7": "11111111-0002-0000-0000-000000000003", # Bengaluru Hub
    "e0527739-4d40-4f1b-bca5-be2952171bf3": "11111111-0002-0000-0000-000000000004", # Mysuru Depot
}

def batch_upsert(admin, table_name: str, records: List[Dict[str, Any]], batch_size: int = 500):
    total = len(records)
    for i in range(0, total, batch_size):
        chunk = records[i:i + batch_size]
        admin.table(table_name).upsert(chunk).execute()
        print(f"  [{table_name}] Upserted {min(i + batch_size, total)}/{total} rows...")

def main():
    print("=" * 70)
    print("ALLADIN — DEDICATED INDIAN DEMO COMPANY & DATA INITIALIZER")
    print("=" * 70)
    admin = get_admin_client()

    # Step 1: Company Record
    print("\n[1/12] Ensuring company record 'ALLADIN India Demo Retail'...")
    comp_data = {
        "id": DEMO_COMPANY_ID,
        "name": "ALLADIN India Demo Retail",
        "slug": "alladin-india-demo-retail",
        "industry": "Supermarket",
        "country": "India",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "subscription_status": "active",
        "is_active": True,
    }
    admin.table("companies").upsert(comp_data).execute()
    print("  -> Company configured: INR (₹), Asia/Kolkata, India.")

    # Step 2: Branches
    print("\n[2/12] Initializing Indian branches (Mangaluru, Bengaluru, Mysuru)...")
    branches = [
        {
            "id": "11111111-0001-0000-0000-000000000001",
            "company_id": DEMO_COMPANY_ID,
            "name": "Mangaluru Central HQ",
            "city": "Mangaluru",
            "country": "India",
            "address": "KSR Road, Hampankatta, Mangaluru, Karnataka 575001",
            "phone": "+91 824 244 5500",
            "is_active": True,
        },
        {
            "id": "11111111-0001-0000-0000-000000000002",
            "company_id": DEMO_COMPANY_ID,
            "name": "Bengaluru Flagship",
            "city": "Bengaluru",
            "country": "India",
            "address": "100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038",
            "phone": "+91 80 2520 8800",
            "is_active": True,
        },
        {
            "id": "11111111-0001-0000-0000-000000000003",
            "company_id": DEMO_COMPANY_ID,
            "name": "Mysuru Depot",
            "city": "Mysuru",
            "country": "India",
            "address": "Sayyaji Rao Road, Mandi Mohalla, Mysuru, Karnataka 570001",
            "phone": "+91 821 242 1100",
            "is_active": True,
        },
    ]
    admin.table("branches").upsert(branches).execute()
    print("  -> 3 Indian branches created.")

    # Step 3: Warehouses
    print("\n[3/12] Initializing Indian warehouses...")
    warehouses = [
        {
            "id": "11111111-0002-0000-0000-000000000001",
            "company_id": DEMO_COMPANY_ID,
            "branch_id": "11111111-0001-0000-0000-000000000001",
            "name": "Mangaluru Central Warehouse",
            "address": "Baikampady Industrial Area, Mangaluru, Karnataka",
            "is_active": True,
        },
        {
            "id": "11111111-0002-0000-0000-000000000002",
            "company_id": DEMO_COMPANY_ID,
            "branch_id": "11111111-0001-0000-0000-000000000001",
            "name": "Mangaluru Reserve Depot",
            "address": "Bunder Wharf Logistics Yard, Mangaluru, Karnataka",
            "is_active": True,
        },
        {
            "id": "11111111-0002-0000-0000-000000000003",
            "company_id": DEMO_COMPANY_ID,
            "branch_id": "11111111-0001-0000-0000-000000000002",
            "name": "Bengaluru Fulfillment Hub",
            "address": "Peenya 3rd Phase Industrial Area, Bengaluru, Karnataka",
            "is_active": True,
        },
        {
            "id": "11111111-0002-0000-0000-000000000004",
            "company_id": DEMO_COMPANY_ID,
            "branch_id": "11111111-0001-0000-0000-000000000003",
            "name": "Mysuru Distribution Center",
            "address": "Hebbal Industrial Area, Mysuru, Karnataka",
            "is_active": True,
        },
    ]
    admin.table("warehouses").upsert(warehouses).execute()
    print("  -> 4 regional warehouses created.")

    # Step 4: Demo Auth User
    print(f"\n[4/12] Ensuring demo user '{DEMO_USER_EMAIL}'...")
    user_id = None
    existing_users = admin.table("users").select("id, email").eq("email", DEMO_USER_EMAIL).execute().data
    if existing_users:
        user_id = existing_users[0]["id"]
    else:
        try:
            resp = admin.auth.admin.create_user({
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASS,
                "email_confirm": True,
                "user_metadata": {"full_name": DEMO_USER_NAME}
            })
            user_id = resp.user.id
        except Exception:
            for u in admin.auth.admin.list_users():
                if u.email == DEMO_USER_EMAIL:
                    user_id = u.id
                    break

    admin.table("users").upsert({
        "id": user_id,
        "email": DEMO_USER_EMAIL,
        "full_name": DEMO_USER_NAME,
        "is_active": True,
    }).execute()

    owner_role = "b1000000-0000-0000-0000-000000000001"
    cu_existing = admin.table("company_users").select("id").eq("company_id", DEMO_COMPANY_ID).eq("user_id", user_id).execute().data
    if not cu_existing:
        admin.table("company_users").insert({
            "company_id": DEMO_COMPANY_ID,
            "user_id": user_id,
            "role_id": owner_role,
            "branch_id": "11111111-0001-0000-0000-000000000001",
        }).execute()
    print(f"  -> User {user_id} assigned as Company Owner.")

    # Also associate pooja.sharma95 if exists so developer can switch seamlessly
    pooja_res = admin.table("users").select("id").eq("email", "pooja.sharma95@horizonretailltd.com").execute().data
    if pooja_res:
        pooja_id = pooja_res[0]["id"]
        pooja_cu = admin.table("company_users").select("id").eq("company_id", DEMO_COMPANY_ID).eq("user_id", pooja_id).execute().data
        if not pooja_cu:
            admin.table("company_users").insert({
                "company_id": DEMO_COMPANY_ID,
                "user_id": pooja_id,
                "role_id": owner_role,
                "branch_id": "11111111-0001-0000-0000-000000000001",
            }).execute()
        print("  -> Secondary developer account linked as member.")

    # Step 5: Categories
    print("\n[5/12] Seeding product and expense categories...")
    categories_df = pd.read_csv(os.path.join(DATASET_DIR, "categories.csv"))
    c1_cats = categories_df[categories_df["company_id"] == SOURCE_COMPANY_ID]
    cat_records = []
    for _, r in c1_cats.iterrows():
        new_id = map_uuid("cat", r["id"])
        cat_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "name": r["name"],
            "type": r.get("type", "product"),
            "description": r.get("description", ""),
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "categories", cat_records)

    # Step 6: Products
    print("\n[6/12] Seeding 100 Indian retail products...")
    products_df = pd.read_csv(os.path.join(DATASET_DIR, "products.csv"))
    c1_prods = products_df[products_df["company_id"] == SOURCE_COMPANY_ID]
    prod_records = []
    for _, r in c1_prods.iterrows():
        new_id = map_uuid("prod", r["id"])
        new_cat_id = map_uuid("cat", r["category_id"])
        prod_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "category_id": new_cat_id,
            "name": r["name"],
            "sku": r["sku"],
            "cost_price": float(r["cost_price"]),
            "selling_price": float(r["selling_price"]),
            "tax_rate": float(r.get("tax_rate", 0.0)),
            "unit": r.get("unit", "pcs"),
            "is_active": True,
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "products", prod_records)

    # Step 7: Customers & Suppliers
    print("\n[7/12] Seeding 170 Indian customers & 17 Indian FMCG suppliers...")
    customers_df = pd.read_csv(os.path.join(DATASET_DIR, "customers.csv"))
    c1_custs = customers_df[customers_df["company_id"] == SOURCE_COMPANY_ID]
    city_remap = {"Mumbai": "Mangaluru", "Pune": "Bengaluru", "Ahmedabad": "Mysuru"}
    cust_records = []
    for _, r in c1_custs.iterrows():
        new_id = map_uuid("cust", r["id"])
        new_city = city_remap.get(r["city"], "Mangaluru")
        cust_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "name": r["name"],
            "email": f"cust_{r['id'][:8]}@retailindia.in",
            "phone": r.get("phone", "+91 98450 12345"),
            "city": new_city,
            "country": "India",
            "currency": "INR",
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "customers", cust_records)

    suppliers_df = pd.read_csv(os.path.join(DATASET_DIR, "suppliers.csv"))
    c1_supps = suppliers_df[suppliers_df["company_id"] == SOURCE_COMPANY_ID]
    supp_records = []
    for _, r in c1_supps.iterrows():
        new_id = map_uuid("supp", r["id"])
        new_city = city_remap.get(r["city"], "Bengaluru")
        supp_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "name": r["name"],
            "email": f"supply_{r['id'][:8]}@fmcgindia.com",
            "phone": r.get("phone", "+91 80 2345 6789"),
            "city": new_city,
            "country": "India",
            "currency": "INR",
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "suppliers", supp_records)

    # Step 8: Sales & Sale Items (2022 to 2026-10-21)
    print("\n[8/12] Seeding sales orders and line items (2022 to 2026-10-21)...")
    sales_df = pd.read_csv(os.path.join(DATASET_DIR, "sales.csv"))
    c1_sales = sales_df[sales_df["company_id"] == SOURCE_COMPANY_ID]
    status_map = {"completed": "delivered", "pending": "draft", "cancelled": "cancelled"}
    sale_records = []
    for _, r in c1_sales.iterrows():
        new_id = map_uuid("sale", r["id"])
        branch_id = BRANCH_MAP.get(r["branch_id"], "11111111-0001-0000-0000-000000000001")
        customer_id = map_uuid("cust", r["customer_id"])
        sale_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "branch_id": branch_id,
            "customer_id": customer_id,
            "sale_number": f"SL-{r['id'][:8].upper()}",
            "sale_date": str(r["sale_date"])[:10],
            "status": status_map.get(r["status"], "delivered"),
            "subtotal": float(r["total_amount"]),
            "discount_amount": float(r.get("discount_amount", 0.0)),
            "tax_amount": float(r.get("tax_amount", 0.0)),
            "total_amount": float(r["net_amount"]),
            "currency": "INR",
            "created_by": user_id,
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "sales", sale_records)

    # Sale Items
    sale_items_df = pd.read_csv(os.path.join(DATASET_DIR, "sale_items.csv"))
    c1_sale_ids = set(c1_sales["id"])
    c1_items = sale_items_df[sale_items_df["sale_id"].isin(c1_sale_ids)]
    item_records = []
    for _, r in c1_items.iterrows():
        new_id = map_uuid("sitem", r["id"])
        new_sale_id = map_uuid("sale", r["sale_id"])
        new_prod_id = map_uuid("prod", r["product_id"])
        item_records.append({
            "id": new_id,
            "sale_id": new_sale_id,
            "product_id": new_prod_id,
            "quantity": float(r["quantity"]),
            "unit_price": float(r["unit_price"]),
            "discount_pct": float(r.get("discount_pct", 0.0)),
            "tax_rate": 0.0,
            "line_total": float(r["line_total"]),
        })
    batch_upsert(admin, "sale_items", item_records)

    # Step 9: Purchases & Purchase Items
    print("\n[9/12] Seeding purchases & purchase line items...")
    purchases_df = pd.read_csv(os.path.join(DATASET_DIR, "purchases.csv"))
    c1_purchases = purchases_df[purchases_df["company_id"] == SOURCE_COMPANY_ID]
    pur_status_map = {"received": "received", "pending": "draft", "cancelled": "cancelled"}
    pur_records = []
    for _, r in c1_purchases.iterrows():
        new_id = map_uuid("pur", r["id"])
        branch_id = BRANCH_MAP.get(r["branch_id"], "11111111-0001-0000-0000-000000000001")
        supplier_id = map_uuid("supp", r["supplier_id"])
        pur_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "branch_id": branch_id,
            "supplier_id": supplier_id,
            "purchase_number": f"PO-{r['id'][:8].upper()}",
            "purchase_date": str(r["purchase_date"])[:10],
            "status": pur_status_map.get(r["status"], "received"),
            "subtotal": float(r["total_amount"]),
            "tax_amount": float(r.get("tax_amount", 0.0)),
            "total_amount": float(r["net_amount"]),
            "currency": "INR",
            "created_by": user_id,
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "purchases", pur_records)

    purchase_items_df = pd.read_csv(os.path.join(DATASET_DIR, "purchase_items.csv"))
    c1_pur_ids = set(c1_purchases["id"])
    c1_pitems = purchase_items_df[purchase_items_df["purchase_id"].isin(c1_pur_ids)]
    pitem_records = []
    for _, r in c1_pitems.iterrows():
        new_id = map_uuid("pitem", r["id"])
        new_pur_id = map_uuid("pur", r["purchase_id"])
        new_prod_id = map_uuid("prod", r["product_id"])
        pitem_records.append({
            "id": new_id,
            "purchase_id": new_pur_id,
            "product_id": new_prod_id,
            "quantity": float(r["quantity"]),
            "unit_cost": float(r["unit_cost"]),
            "tax_rate": 0.0,
            "line_total": float(r["line_total"]),
            "received_qty": float(r["quantity"]),
        })
    batch_upsert(admin, "purchase_items", pitem_records)

    # Step 10: Expenses
    print("\n[10/12] Seeding operational expense vouchers (2022 to 2026-10-21)...")
    expenses_df = pd.read_csv(os.path.join(DATASET_DIR, "expenses.csv"))
    c1_exp = expenses_df[expenses_df["company_id"] == SOURCE_COMPANY_ID]
    exp_records = []
    for _, r in c1_exp.iterrows():
        new_id = map_uuid("exp", r["id"])
        branch_id = BRANCH_MAP.get(r["branch_id"], "11111111-0001-0000-0000-000000000001")
        cat_id = map_uuid("cat", r.get("category_id"))
        exp_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "branch_id": branch_id,
            "category_id": cat_id,
            "description": r["description"],
            "amount": float(r["amount"]),
            "expense_date": str(r["expense_date"])[:10],
            "payment_method": "bank_transfer",
            "status": "approved" if r["status"] in ("approved", "completed", "recorded") else "pending",
            "created_by": user_id,
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "expenses", exp_records)

    # Step 11: Invoices & Payments
    print("\n[11/12] Seeding invoices & customer payments...")
    invoices_df = pd.read_csv(os.path.join(DATASET_DIR, "invoices.csv"))
    c1_inv = invoices_df[invoices_df["company_id"] == SOURCE_COMPANY_ID]
    inv_records = []
    for _, r in c1_inv.iterrows():
        new_id = map_uuid("inv", r["id"])
        sale_id = map_uuid("sale", r["sale_id"])
        cust_id = map_uuid("cust", r["customer_id"])
        tot = float(r["total_amount"])
        paid = float(r.get("paid_amount", tot))
        inv_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "invoice_type": "receivable",
            "invoice_number": r["invoice_number"],
            "invoice_date": str(r["invoice_date"])[:10],
            "due_date": str(r["due_date"])[:10],
            "customer_id": cust_id,
            "sale_id": sale_id,
            "status": r["status"],
            "subtotal": tot,
            "tax_amount": 0.0,
            "total_amount": tot,
            "amount_paid": paid,
            "currency": "INR",
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "invoices", inv_records)

    payments_df = pd.read_csv(os.path.join(DATASET_DIR, "payments.csv"))
    c1_pay = payments_df[payments_df["company_id"] == SOURCE_COMPANY_ID]
    sale_to_inv = {r['sale_id']: r['id'] for _, r in c1_inv.iterrows() if pd.notna(r['sale_id'])}
    pay_records = []
    for _, r in c1_pay.iterrows():
        inv_raw_id = sale_to_inv.get(r["reference_id"])
        if not inv_raw_id:
            continue
        new_id = map_uuid("pay", r["id"])
        inv_id = map_uuid("inv", inv_raw_id)
        pay_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "invoice_id": inv_id,
            "payment_date": str(r["payment_date"])[:10],
            "amount": float(r["amount"]),
            "payment_method": r.get("payment_method", "bank_transfer"),
            "reference": f"PAY-{r['id'][:8].upper()}",
            "currency": "INR",
            "created_by": user_id,
            "created_at": str(r["created_at"]),
        })
    batch_upsert(admin, "payments", pay_records)

    # Step 12: Inventory
    print("\n[12/12] Seeding inventory balances...")
    inv_df = pd.read_csv(os.path.join(DATASET_DIR, "inventory.csv"))
    # Map products and warehouses
    inv_records = []
    for _, r in inv_df.iterrows():
        wh_id = WAREHOUSE_MAP.get(r["warehouse_id"])
        if not wh_id:
            continue
        prod_id = map_uuid("prod", r["product_id"])
        new_id = map_uuid("inv_stock", r["id"])
        inv_records.append({
            "id": new_id,
            "company_id": DEMO_COMPANY_ID,
            "product_id": prod_id,
            "warehouse_id": wh_id,
            "quantity": float(r["quantity_on_hand"]),
            "reorder_level": float(r.get("reorder_level", 25.0)),
        })
    batch_upsert(admin, "inventory", inv_records)

    # Verification: Test login
    print("\n" + "=" * 70)
    print("DEMO VERIFICATION: TESTING AUTHENTICATION")
    print("=" * 70)
    anon = get_anon_client()
    login_res = anon.auth.sign_in_with_password({
        "email": DEMO_USER_EMAIL,
        "password": DEMO_USER_PASS
    })
    token = login_res.session.access_token
    print(f"[OK] Live Supabase Auth Login verified for {DEMO_USER_EMAIL}")
    print(f"     JWT Token acquired: {token[:20]}... (length: {len(token)})")

    # Verify company lookup
    my_companies = admin.table("company_users").select("company_id, roles(name), companies(*)").eq("user_id", user_id).execute().data
    print(f"[OK] User assigned companies: {len(my_companies)}")
    for c in my_companies:
        comp_info = c.get("companies", {})
        print(f"     -> Company: '{comp_info.get('name')}' | Country: {comp_info.get('country')} | Currency: {comp_info.get('currency')} | Timezone: {comp_info.get('timezone')}")

    print("\n" + "=" * 70)
    print("DEDICATED INDIAN DEMO INITIALIZATION COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()
