# -*- coding: utf-8 -*-
"""
validate_synthetic_data.py
==========================
Validates all 17 synthetic CSV files for:
- File existence
- Foreign-key integrity
- Row counts vs. design targets
- Missing values in required columns
- Date ranges (2022-01-01 to 2024-12-31)
- Internal consistency: sales/purchase totals, invoice amounts, stock movements
"""

import os
import sys
import json
from datetime import date

import pandas as pd
import numpy as np

# -----------------------------------------------------------------------
DATA_DIR   = os.path.dirname(os.path.abspath(__file__))
START_DATE = date(2022, 1, 1)
END_DATE   = date(2024, 12, 31)

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = {}     # filename -> {rows, cols, checks}
all_ok  = True   # flips False on any FAIL


def register(filename, df, checks):
    results[filename] = {
        "rows":   len(df),
        "cols":   len(df.columns),
        "checks": checks,
    }


def chk(label, ok, detail=""):
    global all_ok
    tag = PASS if ok else FAIL
    if not ok:
        all_ok = False
    msg = f"    {tag}  {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    return {"label": label, "ok": ok, "detail": detail}


# -----------------------------------------------------------------------
# Load all CSVs
# -----------------------------------------------------------------------

print()
print("=" * 65)
print("  Synthetic Dataset Validation")
print("=" * 65)
print()
print("[LOADING] Reading all CSV files...")
print()

def load(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        print(f"  {FAIL}  {name}  -- FILE NOT FOUND")
        global all_ok
        all_ok = False
        return None
    df = pd.read_csv(path)
    return df

companies_df       = load("companies.csv")
branches_df        = load("branches.csv")
users_df           = load("users.csv")
customers_df       = load("customers.csv")
suppliers_df       = load("suppliers.csv")
categories_df      = load("categories.csv")
products_df        = load("products.csv")
warehouses_df      = load("warehouses.csv")
inventory_df       = load("inventory.csv")
stock_movements_df = load("stock_movements.csv")
sales_df           = load("sales.csv")
sale_items_df      = load("sale_items.csv")
purchases_df       = load("purchases.csv")
purchase_items_df  = load("purchase_items.csv")
payments_df        = load("payments.csv")
expenses_df        = load("expenses.csv")
invoices_df        = load("invoices.csv")

all_dfs = {
    "companies.csv":       companies_df,
    "branches.csv":        branches_df,
    "users.csv":           users_df,
    "customers.csv":       customers_df,
    "suppliers.csv":       suppliers_df,
    "categories.csv":      categories_df,
    "products.csv":        products_df,
    "warehouses.csv":      warehouses_df,
    "inventory.csv":       inventory_df,
    "stock_movements.csv": stock_movements_df,
    "sales.csv":           sales_df,
    "sale_items.csv":      sale_items_df,
    "purchases.csv":       purchases_df,
    "purchase_items.csv":  purchase_items_df,
    "payments.csv":        payments_df,
    "expenses.csv":        expenses_df,
    "invoices.csv":        invoices_df,
}

if any(v is None for v in all_dfs.values()):
    print()
    print(f"{FAIL}  One or more CSV files are missing. Aborting validation.")
    sys.exit(1)

print("  All 17 files loaded OK.")
print()

# -----------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------

def check_no_nulls(df, cols, label_prefix=""):
    chks = []
    for col in cols:
        if col not in df.columns:
            chks.append(chk(f"{label_prefix}column '{col}' exists", False, "MISSING COLUMN"))
            continue
        n_null = df[col].isnull().sum()
        chks.append(chk(
            f"{label_prefix}no nulls in '{col}'",
            n_null == 0,
            f"{n_null} nulls found" if n_null else "",
        ))
    return chks

def check_fk(child_df, child_col, parent_df, parent_col="id", label=""):
    if child_col not in child_df.columns:
        return chk(label or f"FK {child_col}", False, "COLUMN MISSING")
    # Allow NaN FK (nullable FK like reference_id in stock_movements)
    child_vals = set(child_df[child_col].dropna())
    parent_vals = set(parent_df[parent_col])
    orphans = child_vals - parent_vals
    return chk(
        label or f"FK {child_col} -> {parent_col}",
        len(orphans) == 0,
        f"{len(orphans)} orphan IDs" if orphans else "",
    )

def check_date_range(df, date_col, start=START_DATE, end=END_DATE, label=""):
    if date_col not in df.columns:
        return chk(label or f"date range {date_col}", False, "COLUMN MISSING")
    dates = pd.to_datetime(df[date_col], errors="coerce")
    n_invalid = dates.isnull().sum()
    if n_invalid:
        return chk(label or f"date range {date_col}", False, f"{n_invalid} unparseable dates")
    min_d = dates.dt.date.min()
    max_d = dates.dt.date.max()
    ok = (min_d >= start) and (max_d <= end)
    detail = f"range [{min_d} .. {max_d}]"
    return chk(label or f"date range {date_col}", ok, detail)

def check_row_count(df, name, min_rows, max_rows=None):
    n = len(df)
    if max_rows is None:
        ok = n >= min_rows
        detail = f"{n:,} rows (expected >= {min_rows:,})"
    else:
        ok = min_rows <= n <= max_rows
        detail = f"{n:,} rows (expected {min_rows:,} - {max_rows:,})"
    return chk(f"{name} row count", ok, detail)

def check_enum(df, col, valid_values, label=""):
    if col not in df.columns:
        return chk(label or f"enum {col}", False, "COLUMN MISSING")
    invalid = ~df[col].isin(valid_values)
    n_inv = invalid.sum()
    return chk(
        label or f"enum values in '{col}'",
        n_inv == 0,
        f"{n_inv} invalid values: {df[col][invalid].unique().tolist()[:5]}" if n_inv else "",
    )

def check_positive(df, col, label=""):
    if col not in df.columns:
        return chk(label or f"positive {col}", False, "COLUMN MISSING")
    n_neg = (df[col] < 0).sum()
    return chk(
        label or f"'{col}' >= 0",
        n_neg == 0,
        f"{n_neg} negative values" if n_neg else "",
    )

# -----------------------------------------------------------------------
# 1. companies.csv
# -----------------------------------------------------------------------

print("--- companies.csv ---")
c_chks = []
c_chks.append(check_row_count(companies_df, "companies", 3, 3))
c_chks.extend(check_no_nulls(companies_df, ["id", "name", "industry", "country", "currency", "created_at"]))
c_chks.append(chk("3 unique company IDs", companies_df["id"].nunique() == 3))
c_chks.append(check_enum(companies_df, "currency", ["INR", "USD", "AED"]))
register("companies.csv", companies_df, c_chks)

# -----------------------------------------------------------------------
# 2. branches.csv
# -----------------------------------------------------------------------

print()
print("--- branches.csv ---")
b_chks = []
b_chks.append(check_row_count(branches_df, "branches", 9, 9))
b_chks.extend(check_no_nulls(branches_df, ["id", "company_id", "name", "city", "is_headquarters", "created_at"]))
b_chks.append(check_fk(branches_df, "company_id", companies_df))
b_chks.append(chk("exactly 1 HQ per company",
    branches_df.groupby("company_id")["is_headquarters"].sum().eq(1).all()))
register("branches.csv", branches_df, b_chks)

# -----------------------------------------------------------------------
# 3. users.csv
# -----------------------------------------------------------------------

print()
print("--- users.csv ---")
u_chks = []
u_chks.append(check_row_count(users_df, "users", 36, 36))
u_chks.extend(check_no_nulls(users_df, ["id", "company_id", "branch_id", "name", "email", "role"]))
u_chks.append(check_fk(users_df, "company_id", companies_df))
u_chks.append(check_fk(users_df, "branch_id", branches_df))
u_chks.append(check_enum(users_df, "role", ["admin", "manager", "sales", "accountant"]))
u_chks.append(chk("unique user emails", users_df["email"].nunique() == len(users_df)))
register("users.csv", users_df, u_chks)

# -----------------------------------------------------------------------
# 4. customers.csv
# -----------------------------------------------------------------------

print()
print("--- customers.csv ---")
cu_chks = []
cu_chks.append(check_row_count(customers_df, "customers", 500, 520))
cu_chks.extend(check_no_nulls(customers_df, ["id", "company_id", "name", "email", "city", "customer_type", "credit_limit"]))
cu_chks.append(check_fk(customers_df, "company_id", companies_df))
cu_chks.append(check_enum(customers_df, "customer_type", ["individual", "business"]))
cu_chks.append(check_positive(customers_df, "credit_limit"))
cu_chks.append(chk("customers distributed across all 3 companies",
    customers_df["company_id"].nunique() == 3))
register("customers.csv", customers_df, cu_chks)

# -----------------------------------------------------------------------
# 5. suppliers.csv
# -----------------------------------------------------------------------

print()
print("--- suppliers.csv ---")
s_chks = []
s_chks.append(check_row_count(suppliers_df, "suppliers", 51, 51))
s_chks.extend(check_no_nulls(suppliers_df, ["id", "company_id", "name", "contact_email", "payment_terms_days"]))
s_chks.append(check_fk(suppliers_df, "company_id", companies_df))
s_chks.append(check_enum(suppliers_df, "payment_terms_days", [15, 30, 45, 60, 90]))
s_chks.append(chk("multiple suppliers per company",
    suppliers_df.groupby("company_id").size().min() >= 5))
register("suppliers.csv", suppliers_df, s_chks)

# -----------------------------------------------------------------------
# 6. categories.csv
# -----------------------------------------------------------------------

print()
print("--- categories.csv ---")
cat_chks = []
cat_chks.append(check_row_count(categories_df, "categories", 60, 60))
cat_chks.extend(check_no_nulls(categories_df, ["id", "company_id", "name"]))
cat_chks.append(check_fk(categories_df, "company_id", companies_df))
cat_chks.append(chk("20 categories per company",
    categories_df.groupby("company_id").size().eq(20).all()))
register("categories.csv", categories_df, cat_chks)

# -----------------------------------------------------------------------
# 7. products.csv
# -----------------------------------------------------------------------

print()
print("--- products.csv ---")
p_chks = []
p_chks.append(check_row_count(products_df, "products", 290, 310))
p_chks.extend(check_no_nulls(products_df, ["id", "company_id", "category_id", "name", "sku", "cost_price", "selling_price", "unit", "is_active"]))
p_chks.append(check_fk(products_df, "company_id", companies_df))
p_chks.append(check_fk(products_df, "category_id", categories_df))
p_chks.append(check_positive(products_df, "cost_price"))
p_chks.append(check_positive(products_df, "selling_price"))
p_chks.append(chk("selling_price >= cost_price for all products",
    (products_df["selling_price"] >= products_df["cost_price"]).all()))
p_chks.append(chk("unique SKU per company",
    products_df.groupby("company_id")["sku"].nunique().eq(
        products_df.groupby("company_id").size()
    ).all()))
register("products.csv", products_df, p_chks)

# -----------------------------------------------------------------------
# 8. warehouses.csv
# -----------------------------------------------------------------------

print()
print("--- warehouses.csv ---")
wh_chks = []
wh_chks.append(check_row_count(warehouses_df, "warehouses", 12, 20))
wh_chks.extend(check_no_nulls(warehouses_df, ["id", "company_id", "branch_id", "name", "location"]))
wh_chks.append(check_fk(warehouses_df, "company_id", companies_df))
wh_chks.append(check_fk(warehouses_df, "branch_id", branches_df))
register("warehouses.csv", warehouses_df, wh_chks)

# -----------------------------------------------------------------------
# 9. inventory.csv
# -----------------------------------------------------------------------

print()
print("--- inventory.csv ---")
inv_chks = []
inv_chks.append(check_row_count(inventory_df, "inventory", 500, 1000))
inv_chks.extend(check_no_nulls(inventory_df, ["id", "product_id", "warehouse_id", "quantity_on_hand", "reorder_level", "reorder_quantity"]))
inv_chks.append(check_fk(inventory_df, "product_id", products_df))
inv_chks.append(check_fk(inventory_df, "warehouse_id", warehouses_df))
inv_chks.append(check_positive(inventory_df, "quantity_on_hand"))
inv_chks.append(check_positive(inventory_df, "reorder_level"))
inv_chks.append(chk("no duplicate (product_id, warehouse_id) pairs",
    inventory_df.duplicated(subset=["product_id", "warehouse_id"]).sum() == 0))
inv_chks.append(chk("reorder_quantity >= reorder_level",
    (inventory_df["reorder_quantity"] >= inventory_df["reorder_level"]).all()))
register("inventory.csv", inventory_df, inv_chks)

# -----------------------------------------------------------------------
# 10. sales.csv
# -----------------------------------------------------------------------

print()
print("--- sales.csv ---")
sa_chks = []
sa_chks.append(check_row_count(sales_df, "sales", 7000, 9000))
sa_chks.extend(check_no_nulls(sales_df, ["id", "company_id", "branch_id", "customer_id", "user_id",
                                           "sale_date", "status", "total_amount", "net_amount", "payment_status"]))
sa_chks.append(check_fk(sales_df, "company_id", companies_df))
sa_chks.append(check_fk(sales_df, "branch_id", branches_df))
sa_chks.append(check_fk(sales_df, "customer_id", customers_df))
sa_chks.append(check_fk(sales_df, "user_id", users_df))
sa_chks.append(check_date_range(sales_df, "sale_date"))
sa_chks.append(check_enum(sales_df, "status", ["completed", "pending", "cancelled"]))
sa_chks.append(check_enum(sales_df, "payment_status", ["paid", "partial", "unpaid"]))
sa_chks.append(check_positive(sales_df, "net_amount"))
sa_chks.append(chk("net_amount = total_amount + tax_amount",
    ((sales_df["net_amount"] - (sales_df["total_amount"] + sales_df["tax_amount"])).abs() < 0.02).all(),
    "tolerance 0.02"))
sa_chks.append(chk("cancelled sales are all unpaid",
    sales_df[sales_df["status"] == "cancelled"]["payment_status"].eq("unpaid").all()))
sa_chks.append(chk("sales span all 3 years (2022/2023/2024)",
    pd.to_datetime(sales_df["sale_date"]).dt.year.nunique() == 3))
sa_chks.append(chk("seasonal signal: Q4 sales > Q1 sales",
    sales_df[pd.to_datetime(sales_df["sale_date"]).dt.quarter == 4].shape[0] >
    sales_df[pd.to_datetime(sales_df["sale_date"]).dt.quarter == 1].shape[0]))
register("sales.csv", sales_df, sa_chks)

# -----------------------------------------------------------------------
# 11. sale_items.csv
# -----------------------------------------------------------------------

print()
print("--- sale_items.csv ---")
si_chks = []
si_chks.append(check_row_count(sale_items_df, "sale_items", 15000, 22000))
si_chks.extend(check_no_nulls(sale_items_df, ["id", "sale_id", "product_id", "quantity", "unit_price", "line_total"]))
si_chks.append(check_fk(sale_items_df, "sale_id", sales_df))
si_chks.append(check_fk(sale_items_df, "product_id", products_df))
si_chks.append(check_positive(sale_items_df, "quantity"))
si_chks.append(check_positive(sale_items_df, "unit_price"))

# Check line_total = qty * unit_price * (1 - discount_pct)
computed = (sale_items_df["quantity"] * sale_items_df["unit_price"]
            * (1 - sale_items_df["discount_pct"])).round(2)
line_total_ok = ((computed - sale_items_df["line_total"]).abs() < 0.02).all()
si_chks.append(chk("line_total = qty * unit_price * (1 - discount_pct)", line_total_ok, "tolerance 0.02"))

# Check sale_items totals match sales totals
si_agg   = sale_items_df.groupby("sale_id")["line_total"].sum().reset_index()
si_agg.columns = ["id", "items_total"]
merged   = sales_df[["id", "total_amount"]].merge(si_agg, on="id", how="left")
mismatch = ((merged["total_amount"] - merged["items_total"]).abs() > 0.10).sum()
si_chks.append(chk(
    "sale_items line totals match sales.total_amount",
    mismatch == 0,
    f"{mismatch} mismatches" if mismatch else "",
))
register("sale_items.csv", sale_items_df, si_chks)

# -----------------------------------------------------------------------
# 12. purchases.csv
# -----------------------------------------------------------------------

print()
print("--- purchases.csv ---")
pu_chks = []
pu_chks.append(check_row_count(purchases_df, "purchases", 2500, 3500))
pu_chks.extend(check_no_nulls(purchases_df, ["id", "company_id", "branch_id", "supplier_id", "user_id",
                                               "purchase_date", "status", "total_amount", "net_amount"]))
pu_chks.append(check_fk(purchases_df, "company_id", companies_df))
pu_chks.append(check_fk(purchases_df, "branch_id", branches_df))
pu_chks.append(check_fk(purchases_df, "supplier_id", suppliers_df))
pu_chks.append(check_fk(purchases_df, "user_id", users_df))
pu_chks.append(check_date_range(purchases_df, "purchase_date"))
pu_chks.append(check_enum(purchases_df, "status", ["received", "pending", "cancelled"]))
pu_chks.append(check_enum(purchases_df, "payment_status", ["paid", "partial", "unpaid"]))
pu_chks.append(check_positive(purchases_df, "net_amount"))
pu_chks.append(chk("cancelled purchases are all unpaid",
    purchases_df[purchases_df["status"] == "cancelled"]["payment_status"].eq("unpaid").all()))
register("purchases.csv", purchases_df, pu_chks)

# -----------------------------------------------------------------------
# 13. purchase_items.csv
# -----------------------------------------------------------------------

print()
print("--- purchase_items.csv ---")
pi_chks = []
pi_chks.append(check_row_count(purchase_items_df, "purchase_items", 5000, 10000))
pi_chks.extend(check_no_nulls(purchase_items_df, ["id", "purchase_id", "product_id", "quantity", "unit_cost", "line_total"]))
pi_chks.append(check_fk(purchase_items_df, "purchase_id", purchases_df))
pi_chks.append(check_fk(purchase_items_df, "product_id", products_df))
pi_chks.append(check_positive(purchase_items_df, "quantity"))
pi_chks.append(check_positive(purchase_items_df, "unit_cost"))

computed_pi = (purchase_items_df["quantity"] * purchase_items_df["unit_cost"]).round(2)
pi_line_ok  = ((computed_pi - purchase_items_df["line_total"]).abs() < 0.02).all()
pi_chks.append(chk("line_total = qty * unit_cost", pi_line_ok, "tolerance 0.02"))

pi_agg  = purchase_items_df.groupby("purchase_id")["line_total"].sum().reset_index()
pi_agg.columns = ["id", "items_total"]
pu_merged = purchases_df[["id", "total_amount"]].merge(pi_agg, on="id", how="left")
pu_mismatch = ((pu_merged["total_amount"] - pu_merged["items_total"]).abs() > 0.10).sum()
pi_chks.append(chk(
    "purchase_items totals match purchases.total_amount",
    pu_mismatch == 0,
    f"{pu_mismatch} mismatches" if pu_mismatch else "",
))
register("purchase_items.csv", purchase_items_df, pi_chks)

# -----------------------------------------------------------------------
# 14. payments.csv
# -----------------------------------------------------------------------

print()
print("--- payments.csv ---")
pay_chks = []
pay_chks.append(check_row_count(payments_df, "payments", 5000, 15000))
pay_chks.extend(check_no_nulls(payments_df, ["id", "company_id", "reference_type", "reference_id",
                                               "amount", "payment_method", "payment_date"]))
pay_chks.append(check_fk(payments_df, "company_id", companies_df))
pay_chks.append(check_enum(payments_df, "reference_type", ["sale", "purchase"]))
pay_chks.append(check_enum(payments_df, "payment_method", ["cash", "card", "bank_transfer", "cheque"]))
pay_chks.append(check_date_range(payments_df, "payment_date"))
pay_chks.append(check_positive(payments_df, "amount"))

# FK: reference_id must point to valid sale or purchase
sale_ids     = set(sales_df["id"])
purchase_ids = set(purchases_df["id"])
sale_pay_ids = set(payments_df[payments_df["reference_type"] == "sale"]["reference_id"])
pur_pay_ids  = set(payments_df[payments_df["reference_type"] == "purchase"]["reference_id"])
pay_chks.append(chk("sale payment reference_ids are valid sale IDs",
    sale_pay_ids <= sale_ids,
    f"{len(sale_pay_ids - sale_ids)} orphans" if sale_pay_ids - sale_ids else ""))
pay_chks.append(chk("purchase payment reference_ids are valid purchase IDs",
    pur_pay_ids <= purchase_ids,
    f"{len(pur_pay_ids - purchase_ids)} orphans" if pur_pay_ids - purchase_ids else ""))

# Payment date must be >= sale/purchase date
sale_dates   = sales_df.set_index("id")["sale_date"].to_dict()
pur_dates    = purchases_df.set_index("id")["purchase_date"].to_dict()
sale_payments = payments_df[payments_df["reference_type"] == "sale"].copy()
sale_payments["ref_date"] = sale_payments["reference_id"].map(sale_dates)
early_sale_pay = (pd.to_datetime(sale_payments["payment_date"]) <
                  pd.to_datetime(sale_payments["ref_date"])).sum()
pay_chks.append(chk("payment_date >= sale_date for all sale payments",
    early_sale_pay == 0, f"{early_sale_pay} payments before sale date" if early_sale_pay else ""))
register("payments.csv", payments_df, pay_chks)

# -----------------------------------------------------------------------
# 15. expenses.csv
# -----------------------------------------------------------------------

print()
print("--- expenses.csv ---")
ex_chks = []
ex_chks.append(check_row_count(expenses_df, "expenses", 2500, 20000))
ex_chks.extend(check_no_nulls(expenses_df, ["id", "company_id", "branch_id", "user_id",
                                              "category", "amount", "expense_date", "status"]))
ex_chks.append(check_fk(expenses_df, "company_id", companies_df))
ex_chks.append(check_fk(expenses_df, "branch_id", branches_df))
ex_chks.append(check_fk(expenses_df, "user_id", users_df))
ex_chks.append(check_date_range(expenses_df, "expense_date"))
ex_chks.append(check_enum(expenses_df, "status", ["approved", "pending", "rejected"]))
ex_chks.append(check_positive(expenses_df, "amount"))
ex_chks.append(chk("fixed expense categories present (Rent/Salaries/Utilities)",
    {"Rent", "Salaries", "Utilities"}.issubset(set(expenses_df["category"]))))
ex_chks.append(chk("expenses cover all 3 years",
    pd.to_datetime(expenses_df["expense_date"]).dt.year.nunique() == 3))
register("expenses.csv", expenses_df, ex_chks)

# -----------------------------------------------------------------------
# 16. stock_movements.csv
# -----------------------------------------------------------------------

print()
print("--- stock_movements.csv ---")
sm_chks = []
sm_chks.append(check_row_count(stock_movements_df, "stock_movements", 15000, 40000))
sm_chks.extend(check_no_nulls(stock_movements_df, ["id", "product_id", "warehouse_id",
                                                     "movement_type", "quantity", "reason", "moved_at"]))
sm_chks.append(check_fk(stock_movements_df, "product_id", products_df))
sm_chks.append(check_fk(stock_movements_df, "warehouse_id", warehouses_df))
sm_chks.append(check_enum(stock_movements_df, "movement_type", ["in", "out"]))
sm_chks.append(check_enum(stock_movements_df, "reason",
    ["sale", "purchase", "adjustment", "return", "transfer", "write_off"]))
sm_chks.append(check_date_range(stock_movements_df, "moved_at"))
sm_chks.append(check_positive(stock_movements_df, "quantity"))

# reference_id nullable check: adjustment/return/transfer/write_off can be null
sm_nullref = stock_movements_df[stock_movements_df["reason"].isin(["sale", "purchase"])]["reference_id"].isnull().sum()
sm_chks.append(chk("sale/purchase movements have non-null reference_id",
    sm_nullref == 0, f"{sm_nullref} null refs" if sm_nullref else ""))

# Number of out movements (from sales) should roughly match sale_items rows
n_out = (stock_movements_df["movement_type"] == "out").sum()
n_in  = (stock_movements_df["movement_type"] == "in").sum()
sm_chks.append(chk("both 'in' and 'out' movements present",
    n_in > 1000 and n_out > 1000,
    f"in={n_in:,}  out={n_out:,}"))
register("stock_movements.csv", stock_movements_df, sm_chks)

# -----------------------------------------------------------------------
# 17. invoices.csv
# -----------------------------------------------------------------------

print()
print("--- invoices.csv ---")
inv_chks = []
inv_chks.append(check_row_count(invoices_df, "invoices", 7000, 9000))
inv_chks.extend(check_no_nulls(invoices_df, ["id", "company_id", "sale_id", "customer_id",
                                               "invoice_number", "invoice_date", "due_date",
                                               "total_amount", "paid_amount", "status"]))
inv_chks.append(check_fk(invoices_df, "company_id", companies_df))
inv_chks.append(check_fk(invoices_df, "sale_id", sales_df))
inv_chks.append(check_fk(invoices_df, "customer_id", customers_df))
inv_chks.append(check_enum(invoices_df, "status", ["paid", "partial", "overdue", "cancelled"]))
inv_chks.append(check_date_range(invoices_df, "invoice_date"))
inv_chks.append(check_positive(invoices_df, "total_amount"))
inv_chks.append(chk("paid_amount <= total_amount for all invoices",
    (invoices_df["paid_amount"] <= invoices_df["total_amount"] + 0.01).all()))
inv_chks.append(chk("cancelled invoices have paid_amount = 0",
    invoices_df[invoices_df["status"] == "cancelled"]["paid_amount"].eq(0).all()))
inv_chks.append(chk("1:1 mapping between sales and invoices",
    len(invoices_df) == len(sales_df),
    f"invoices={len(invoices_df)} sales={len(sales_df)}"))
inv_chks.append(chk("invoice.total_amount = sales.net_amount",
    invoices_df.merge(sales_df[["id", "net_amount"]], left_on="sale_id", right_on="id")
    .pipe(lambda d: ((d["total_amount"] - d["net_amount"]).abs() < 0.02).all()),
    "tolerance 0.02"))
inv_chks.append(chk("unique invoice_numbers",
    invoices_df["invoice_number"].nunique() == len(invoices_df)))
register("invoices.csv", invoices_df, inv_chks)

# -----------------------------------------------------------------------
# Cross-table consistency checks
# -----------------------------------------------------------------------

print()
print("--- Cross-table consistency ---")
x_chks = []

# Branch -> Company isolation: each branch's customers/sales belong to same company
branches_company = branches_df.set_index("id")["company_id"].to_dict()
sales_branch_co  = sales_df.copy()
sales_branch_co["branch_company"] = sales_branch_co["branch_id"].map(branches_company)
x_chks.append(chk("sales: branch_id and company_id belong to same company",
    (sales_branch_co["company_id"] == sales_branch_co["branch_company"]).all()))

# Customers belong to same company as their sales
cust_company = customers_df.set_index("id")["company_id"].to_dict()
sales_cust_co = sales_df.copy()
sales_cust_co["cust_company"] = sales_cust_co["customer_id"].map(cust_company)
x_chks.append(chk("sales: customer_id belongs to same company as sale",
    (sales_cust_co["company_id"] == sales_cust_co["cust_company"]).all()))

# Products in sale_items belong to same company as the sale
prod_company = products_df.set_index("id")["company_id"].to_dict()
si_with_sale = sale_items_df.merge(sales_df[["id", "company_id"]], left_on="sale_id", right_on="id")
si_with_sale["prod_company"] = si_with_sale["product_id"].map(prod_company)
x_chks.append(chk("sale_items: product company matches sale company",
    (si_with_sale["company_id"] == si_with_sale["prod_company"]).all()))

# Suppliers belong to same company as their purchases
sup_company  = suppliers_df.set_index("id")["company_id"].to_dict()
pu_with_sup  = purchases_df.copy()
pu_with_sup["sup_company"] = pu_with_sup["supplier_id"].map(sup_company)
x_chks.append(chk("purchases: supplier belongs to same company",
    (pu_with_sup["company_id"] == pu_with_sup["sup_company"]).all()))

# Inventory warehouse belongs to same company as product
wh_company   = warehouses_df.set_index("id")["company_id"].to_dict()
inv_check    = inventory_df.copy()
inv_check["prod_co"] = inv_check["product_id"].map(prod_company)
inv_check["wh_co"]   = inv_check["warehouse_id"].map(wh_company)
x_chks.append(chk("inventory: product and warehouse belong to same company",
    (inv_check["prod_co"] == inv_check["wh_co"]).all()))

for c in x_chks:
    pass  # already printed by chk()

# -----------------------------------------------------------------------
# Final summary
# -----------------------------------------------------------------------

print()
print("=" * 65)
print("  FINAL VALIDATION SUMMARY")
print("=" * 65)
print()
print(f"  {'File':<28} {'Rows':>8}  {'Cols':>5}  {'Pass':>5}  {'Fail':>5}  {'Status'}")
print(f"  {'-'*28} {'-'*8}  {'-'*5}  {'-'*5}  {'-'*5}  {'-'*10}")

overall_pass = True
for filename, info in results.items():
    n_pass  = sum(1 for c in info["checks"] if c["ok"])
    n_fail  = sum(1 for c in info["checks"] if not c["ok"])
    status  = "PASS" if n_fail == 0 else "FAIL"
    if n_fail > 0:
        overall_pass = False
    print(f"  {filename:<28} {info['rows']:>8,}  {info['cols']:>5}  {n_pass:>5}  {n_fail:>5}  {status}")

print(f"  {'-'*28} {'-'*8}  {'-'*5}  {'-'*5}  {'-'*5}  {'-'*10}")

# Cross-table checks summary
x_pass = sum(1 for c in x_chks if c["ok"])
x_fail = sum(1 for c in x_chks if not c["ok"])
if x_fail:
    overall_pass = False
print(f"  {'cross-table checks':<28} {'':>8}  {'':>5}  {x_pass:>5}  {x_fail:>5}  {'PASS' if x_fail==0 else 'FAIL'}")
print()

total_rows = sum(info["rows"] for info in results.values())
print(f"  Total rows across all 17 files : {total_rows:,}")
print()

if overall_pass:
    print("  OVERALL RESULT: ALL CHECKS PASSED")
else:
    print("  OVERALL RESULT: SOME CHECKS FAILED -- review output above")

print()
