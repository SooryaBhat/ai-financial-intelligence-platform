"""
seed_supermarket_to_supabase.py
================================
Uploads the complete generated Supermarket ERP dataset to Supabase.
Creates a new dedicated demo user and company account:
  User: supermarket.demo@alladin.ai
  Pass: Password123!
  Company: ALLADIN Supermarket Retail Ltd (ID: 33333333-0000-0000-0000-000000000001)
"""

import os
import sys
import json
import time
import pandas as pd
from uuid import UUID

# Include backend in path to import database clients and auth
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, BACKEND_DIR)

from app.database.client import get_admin_client
from app.auth.service import auth_service
from app.schemas.auth import LoginRequest

ERP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets", "supermarket_erp"))

DEMO_EMAIL = "supermarket.demo@alladin.ai"
DEMO_PASSWORD = "Password123!"
DEMO_FULL_NAME = "Supermarket Operations Director"

COMPANY_ID = "33333333-0000-0000-0000-000000000001"
ENTERPRISE_PLAN_ID = "a1000000-0000-0000-0000-000000000004"
OWNER_ROLE_ID = "b1000000-0000-0000-0000-000000000001"

def get_table_columns(admin, table_name):
    try:
        sample = admin.table(table_name).select("*").limit(1).execute()
        if sample.data and len(sample.data) > 0:
            return set(sample.data[0].keys())
    except Exception:
        pass
    return None

def batch_upsert(admin, table_name, records, valid_cols=None, batch_size=50):
    total = len(records)
    print(f"Uploading {total} records to table '{table_name}' in batches of {batch_size}...")
    
    # Filter columns if schema known
    filtered = []
    for r in records:
        if valid_cols:
            clean_r = {k: v for k, v in r.items() if k in valid_cols and k != "amount_due"}
        else:
            clean_r = {k: v for k, v in r.items() if k != "amount_due"}
        filtered.append(clean_r)

    for i in range(0, total, batch_size):
        chunk = filtered[i:i + batch_size]
        res = admin.table(table_name).upsert(chunk).execute()
        time.sleep(0.04)
    print(f"  -> Successfully uploaded {total} records to '{table_name}'.")

def seed():
    admin = get_admin_client()
    print("=== Connected to Supabase Admin Client ===")

    # 1. Ensure Demo User in Auth
    user_id = None
    try:
        users_list = admin.auth.admin.list_users()
        for u in users_list:
            if u.email.lower() == DEMO_EMAIL.lower():
                user_id = u.id
                print(f"Found existing auth user: {DEMO_EMAIL} (ID: {user_id})")
                admin.auth.admin.update_user_by_id(user_id, {"password": DEMO_PASSWORD})
                print("Updated password for existing user.")
                break
    except Exception as e:
        print("Error listing users:", e)

    if not user_id:
        print(f"Creating new auth user: {DEMO_EMAIL}...")
        resp = admin.auth.admin.create_user({
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "email_confirm": True,
            "user_metadata": {
                "full_name": DEMO_FULL_NAME,
                "phone": "+91 99999 88888"
            }
        })
        user_id = resp.user.id
        print(f"Created auth user ID: {user_id}")

    # Ensure in public.users
    admin.table("users").upsert({
        "id": user_id,
        "email": DEMO_EMAIL,
        "full_name": DEMO_FULL_NAME,
        "phone": "+91 99999 88888",
        "is_active": True
    }).execute()
    print("Synced to public.users.")

    # 2. Company
    df_comp = pd.read_csv(os.path.join(ERP_DIR, "companies.csv"))
    comp_record = df_comp.to_dict("records")[0]
    comp_record["plan_id"] = ENTERPRISE_PLAN_ID
    admin.table("companies").upsert(comp_record).execute()
    print(f"Synced company: {comp_record['name']} ({comp_record['id']})")

    # 3. Company User Membership (Owner)
    admin.table("company_users").upsert({
        "company_id": COMPANY_ID,
        "user_id": user_id,
        "role_id": OWNER_ROLE_ID,
        "is_active": True
    }, on_conflict="company_id,user_id").execute()
    print("Assigned Owner role in company_users.")

    # Table upload order for referential integrity
    tables = [
        ("branches", "branches.csv", 50),
        ("warehouses", "warehouses.csv", 50),
        ("categories", "categories.csv", 50),
        ("products", "products.csv", 50),
        ("customers", "customers.csv", 50),
        ("suppliers", "suppliers.csv", 50),
        ("purchases", "purchases.csv", 50),
        ("purchase_items", "purchase_items.csv", 100),
        ("sales", "sales.csv", 100),
        ("sale_items", "sale_items.csv", 100),
        ("inventory", "inventory.csv", 50),
        ("stock_movements", "stock_movements.csv", 150),
        ("invoices", "invoices.csv", 100),
        ("payments", "payments.csv", 100),
        ("expenses", "expenses.csv", 50)
    ]

    for table_name, csv_name, batch_size in tables:
        csv_path = os.path.join(ERP_DIR, csv_name)
        df = pd.read_csv(csv_path)
        valid_cols = get_table_columns(admin, table_name)
        # Convert NaN to None
        records = df.where(pd.notnull(df), None).to_dict("records")
        batch_upsert(admin, table_name, records, valid_cols, batch_size)

    print("\n=== All 15 ERP Tables Uploaded Successfully! ===")

    # 4. Verification Check
    print("\nVerifying Supabase upload and authentication...")
    login_resp = auth_service.login(LoginRequest(email=DEMO_EMAIL, password=DEMO_PASSWORD))
    assert login_resp.get("access_token"), "Login token not received!"
    print(f"Login Verification PASSED! Access token issued: {login_resp['access_token'][:30]}...")

    me_data = auth_service.get_user_me(user_id, DEMO_EMAIL)
    print("User Companies in Supabase:")
    for c in me_data["companies"]:
        print(f"  - {c['name']} (ID: {c['company_id']}, Role: {c['role_name']})")

    # Verify counts in Supabase
    sales_count_db = admin.table("sales").select("id", count="exact").eq("company_id", COMPANY_ID).execute()
    inv_count_db = admin.table("inventory").select("id", count="exact").eq("company_id", COMPANY_ID).execute()
    exp_count_db = admin.table("expenses").select("id", count="exact").eq("company_id", COMPANY_ID).execute()
    print("\nVerified Database Counts for Company:")
    print(f"  Sales orders in DB:      {sales_count_db.count}")
    print(f"  Inventory balances in DB: {inv_count_db.count}")
    print(f"  Expense records in DB:   {exp_count_db.count}")

    print("\n========================================================")
    print("CREDENTIALS FOR DEMO:")
    print(f"  Login Email:    {DEMO_EMAIL}")
    print(f"  Password:       {DEMO_PASSWORD}")
    print(f"  Company Name:   ALLADIN Supermarket Retail Ltd")
    print(f"  Company ID:     {COMPANY_ID}")
    print("========================================================")

if __name__ == "__main__":
    seed()
