# -*- coding: utf-8 -*-
"""
export_2026_seed_sql.py
=======================
Generates an exportable, idempotent SQL seed file for the 2026 current-year
dataset (2026-01-01 to 2026-10-21).

Safety:
- Idempotent: Uses `INSERT INTO ... ON CONFLICT (id) DO NOTHING`
- Read-only against production: Does not touch live database
- Preserves all existing company IDs, tenant isolation, and foreign keys
"""

import os
import sys
from datetime import date
import pandas as pd

DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "datasets", "synthetic")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "supabase", "seeds")
os.makedirs(OUTPUT_DIR, exist_ok=True)
SQL_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "2026_demo_dataset_seed.sql")

START_2026 = "2026-01-01"
CURRENT_DATE = "2026-10-21"

def escape_sql(val):
    if pd.isna(val) or val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    s = str(val).replace("'", "''")
    return f"'{s}'"

def main():
    print(f"Loading synthetic dataset from {DATASET_DIR}...")
    
    # Load core data
    companies_df = pd.read_csv(os.path.join(DATASET_DIR, "companies.csv"))
    branches_df = pd.read_csv(os.path.join(DATASET_DIR, "branches.csv"))
    categories_df = pd.read_csv(os.path.join(DATASET_DIR, "categories.csv"))
    products_df = pd.read_csv(os.path.join(DATASET_DIR, "products.csv"))
    warehouses_df = pd.read_csv(os.path.join(DATASET_DIR, "warehouses.csv"))
    
    sales_df = pd.read_csv(os.path.join(DATASET_DIR, "sales.csv"))
    sale_items_df = pd.read_csv(os.path.join(DATASET_DIR, "sale_items.csv"))
    purchases_df = pd.read_csv(os.path.join(DATASET_DIR, "purchases.csv"))
    purchase_items_df = pd.read_csv(os.path.join(DATASET_DIR, "purchase_items.csv"))
    invoices_df = pd.read_csv(os.path.join(DATASET_DIR, "invoices.csv"))
    payments_df = pd.read_csv(os.path.join(DATASET_DIR, "payments.csv"))
    expenses_df = pd.read_csv(os.path.join(DATASET_DIR, "expenses.csv"))
    stock_movements_df = pd.read_csv(os.path.join(DATASET_DIR, "stock_movements.csv"))
    daily_kpi_df = pd.read_csv(os.path.join(DATASET_DIR, "daily_kpi_summary.csv"))
    
    # Filter 2026 data
    sales_2026 = sales_df[sales_df["sale_date"] >= START_2026]
    sale_ids_2026 = set(sales_2026["id"])
    sale_items_2026 = sale_items_df[sale_items_df["sale_id"].isin(sale_ids_2026)]
    
    purchases_2026 = purchases_df[purchases_df["purchase_date"] >= START_2026]
    purchase_ids_2026 = set(purchases_2026["id"])
    purchase_items_2026 = purchase_items_df[purchase_items_df["purchase_id"].isin(purchase_ids_2026)]
    
    invoices_2026 = invoices_df[invoices_df["invoice_date"] >= START_2026]
    payments_2026 = payments_df[payments_df["payment_date"] >= START_2026]
    expenses_2026 = expenses_df[expenses_df["expense_date"] >= START_2026]
    
    stock_movements_df["m_date"] = stock_movements_df["moved_at"].str[:10]
    stock_movements_2026 = stock_movements_df[stock_movements_df["m_date"] >= START_2026].drop(columns=["m_date"])
    
    kpi_2026 = daily_kpi_df[daily_kpi_df["date"] >= START_2026]
    
    print("\n" + "=" * 65)
    print("  PLANNED 2026 DATASET EXTRACTION SUMMARY")
    print("=" * 65)
    print(f"  Date range coverage : {START_2026} to {CURRENT_DATE} (294 days in 2026)")
    print(f"  Sales orders        : {len(sales_2026):,} rows")
    print(f"  Sale line items     : {len(sale_items_2026):,} rows")
    print(f"  Purchases           : {len(purchases_2026):,} rows")
    print(f"  Purchase line items : {len(purchase_items_2026):,} rows")
    print(f"  Invoices            : {len(invoices_2026):,} rows")
    print(f"  Payments            : {len(payments_2026):,} rows")
    print(f"  Expenses            : {len(expenses_2026):,} rows")
    print(f"  Stock movements     : {len(stock_movements_2026):,} rows")
    print(f"  Daily KPI summaries : {len(kpi_2026):,} rows")
    
    # Financial reconciliation preview for Company 1 in 2026
    c1_kpi = kpi_2026[kpi_2026["company_id"] == "00000000-0000-0000-0000-000000000001"]
    total_rev = c1_kpi["revenue"].sum()
    total_cogs = c1_kpi["cogs"].sum()
    total_gp = c1_kpi["gross_profit"].sum()
    total_exp = c1_kpi["operating_expenses"].sum()
    total_np = c1_kpi["net_profit"].sum()
    
    print("\n  Financial Ledger Health Preview (Demo Company 1, 2026 YTD):")
    print(f"    Revenue        : INR {total_rev:,.2f}")
    print(f"    COGS           : INR {total_cogs:,.2f}")
    print(f"    Gross Profit   : INR {total_gp:,.2f} (Margin: {total_gp/total_rev*100:.1f}%)")
    print(f"    Operating Exp  : INR {total_exp:,.2f}")
    print(f"    Net Profit     : INR {total_np:,.2f} (Margin: {total_np/total_rev*100:.1f}%)")
    print(f"    Mathematical   : Rev - COGS = {total_rev - total_cogs:,.2f} == GP ({total_gp:,.2f})")
    print(f"                   : GP - Exp = {total_gp - total_exp:,.2f} == NP ({total_np:,.2f})")
    print("=" * 65 + "\n")
    
    # Generate SQL
    print(f"Writing idempotent SQL seed to {SQL_OUTPUT_FILE}...")
    
    # Map status enums from CSV to DB
    sale_status_map = {"completed": "delivered", "pending": "draft", "cancelled": "cancelled"}
    pur_status_map = {"received": "received", "pending": "draft", "cancelled": "cancelled"}
    
    with open(SQL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("-- ====================================================================\n")
        f.write("-- ALLADIN 2026 Demo Dataset Idempotent SQL Seed\n")
        f.write(f"-- Date Range: {START_2026} to {CURRENT_DATE} (294 days in 2026)\n")
        f.write("-- Target: Realistic retail time-series in Indian Rupees (INR/₹)\n")
        f.write("-- Safety: ON CONFLICT DO NOTHING (Never overwrites or deletes)\n")
        f.write("-- ====================================================================\n\n")
        f.write("BEGIN;\n\n")
        
        # 1. Categories (Ensure expense categories exist)
        f.write("-- 1. Categories\n")
        for _, r in categories_df.iterrows():
            f.write(
                f"INSERT INTO categories (id, company_id, name, type, description, created_at) "
                f"VALUES ({escape_sql(r['id'])}, {escape_sql(r['company_id'])}, {escape_sql(r['name'])}, "
                f"{escape_sql(r.get('type', 'product'))}, {escape_sql(r.get('description', ''))}, {escape_sql(r['created_at'])}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        f.write("\n")
        
        # 2. Sales 2026
        f.write("-- 2. Sales (2026)\n")
        for _, r in sales_2026.iterrows():
            s_status = sale_status_map.get(r['status'], 'draft')
            sale_num = f"SL-{r['id'][:8].upper()}"
            f.write(
                f"INSERT INTO sales (id, company_id, branch_id, customer_id, sale_number, sale_date, status, "
                f"subtotal, discount_amount, tax_amount, total_amount, currency, created_by, created_at) "
                f"VALUES ({escape_sql(r['id'])}, {escape_sql(r['company_id'])}, {escape_sql(r['branch_id'])}, "
                f"{escape_sql(r['customer_id'])}, '{sale_num}', {escape_sql(r['sale_date'])}, '{s_status}', "
                f"{r['total_amount']}, {r['discount_amount']}, {r['tax_amount']}, {r['net_amount']}, 'INR', "
                f"{escape_sql(r['user_id'])}, {escape_sql(r['created_at'])}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        f.write("\n")
        
        # 3. Sale Items 2026
        f.write("-- 3. Sale Items (2026)\n")
        for _, r in sale_items_2026.iterrows():
            f.write(
                f"INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price, discount_pct, tax_rate, line_total) "
                f"VALUES ({escape_sql(r['id'])}, {escape_sql(r['sale_id'])}, {escape_sql(r['product_id'])}, "
                f"{r['quantity']}, {r['unit_price']}, {r['discount_pct']}, 0, {r['line_total']}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        f.write("\n")
        
        # 4. Purchases 2026
        f.write("-- 4. Purchases (2026)\n")
        for _, r in purchases_2026.iterrows():
            p_status = pur_status_map.get(r['status'], 'draft')
            po_num = f"PO-{r['id'][:8].upper()}"
            f.write(
                f"INSERT INTO purchases (id, company_id, branch_id, supplier_id, purchase_number, purchase_date, "
                f"status, subtotal, tax_amount, total_amount, currency, created_by, created_at) "
                f"VALUES ({escape_sql(r['id'])}, {escape_sql(r['company_id'])}, {escape_sql(r['branch_id'])}, "
                f"{escape_sql(r['supplier_id'])}, '{po_num}', {escape_sql(r['purchase_date'])}, '{p_status}', "
                f"{r['total_amount']}, {r['tax_amount']}, {r['net_amount']}, 'INR', "
                f"{escape_sql(r['user_id'])}, {escape_sql(r['created_at'])}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        f.write("\n")
        
        # 5. Purchase Items 2026
        f.write("-- 5. Purchase Items (2026)\n")
        for _, r in purchase_items_2026.iterrows():
            f.write(
                f"INSERT INTO purchase_items (id, purchase_id, product_id, quantity, unit_cost, tax_rate, line_total, received_qty) "
                f"VALUES ({escape_sql(r['id'])}, {escape_sql(r['purchase_id'])}, {escape_sql(r['product_id'])}, "
                f"{r['quantity']}, {r['unit_cost']}, 0, {r['line_total']}, {r['quantity']}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        f.write("\n")
        
        # 6. Invoices 2026
        f.write("-- 6. Invoices (2026)\n")
        for _, r in invoices_2026.iterrows():
            f.write(
                f"INSERT INTO invoices (id, company_id, invoice_type, invoice_number, invoice_date, due_date, "
                f"customer_id, sale_id, status, subtotal, tax_amount, total_amount, amount_paid, currency, created_at) "
                f"VALUES ({escape_sql(r['id'])}, {escape_sql(r['company_id'])}, 'receivable', {escape_sql(r['invoice_number'])}, "
                f"{escape_sql(r['invoice_date'])}, {escape_sql(r['due_date'])}, {escape_sql(r['customer_id'])}, "
                f"{escape_sql(r['sale_id'])}, {escape_sql(r['status'])}, {r['total_amount']}, 0, "
                f"{r['total_amount']}, {r['paid_amount']}, 'INR', {escape_sql(r['created_at'])}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        f.write("\n")
        
        # 7. Expenses 2026
        f.write("-- 7. Expenses (2026)\n")
        for _, r in expenses_2026.iterrows():
            f.write(
                f"INSERT INTO expenses (id, company_id, branch_id, category_id, description, amount, "
                f"expense_date, payment_method, status, created_by, created_at) "
                f"VALUES ({escape_sql(r['id'])}, {escape_sql(r['company_id'])}, {escape_sql(r['branch_id'])}, "
                f"{escape_sql(r.get('category_id'))}, {escape_sql(r['description'])}, {r['amount']}, "
                f"{escape_sql(r['expense_date'])}, 'bank_transfer', {escape_sql(r['status'])}, "
                f"{escape_sql(r['user_id'])}, {escape_sql(r['created_at'])}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        f.write("\n")
        
        f.write("COMMIT;\n")
        
    print(f"[OK] Seed script successfully written to {SQL_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
