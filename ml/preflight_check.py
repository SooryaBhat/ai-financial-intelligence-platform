"""
preflight_check.py
==================
Verify dataset column names and check for common notebook issues
before running the ML pipeline.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

DATA_DIR = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\datasets\synthetic')

print("=" * 60)
print("PREFLIGHT DATASET CHECK")
print("=" * 60)

# Load key datasets
sales = pd.read_csv(DATA_DIR / 'sales.csv')
expenses = pd.read_csv(DATA_DIR / 'expenses.csv')
inventory = pd.read_csv(DATA_DIR / 'inventory.csv')
products = pd.read_csv(DATA_DIR / 'products.csv')
invoices = pd.read_csv(DATA_DIR / 'invoices.csv')
stock_movements = pd.read_csv(DATA_DIR / 'stock_movements.csv')
sale_items = pd.read_csv(DATA_DIR / 'sale_items.csv')
branches = pd.read_csv(DATA_DIR / 'branches.csv')

print("\n[sales] columns:", list(sales.columns))
print("[expenses] columns:", list(expenses.columns))
print("[inventory] columns:", list(inventory.columns))
print("[products] columns:", list(products.columns))
print("[invoices] columns:", list(invoices.columns))
print("[stock_movements] columns:", list(stock_movements.columns))
print("[sale_items] columns:", list(sale_items.columns))

# Check specific columns notebooks reference
print("\n=== COLUMN EXISTENCE CHECKS ===")
checks = [
    (sales, 'sales', 'gross_amount'),
    (sales, 'sales', 'total_amount'),
    (sales, 'sales', 'discount_amount'),
    (sales, 'sales', 'net_amount'),
    (sales, 'sales', 'tax_amount'),
    (inventory, 'inventory', 'quantity_reserved'),
    (inventory, 'inventory', 'quantity_on_hand'),
    (inventory, 'inventory', 'reorder_level'),
    (invoices, 'invoices', 'paid_amount'),
    (invoices, 'invoices', 'status'),
]
for df, name, col in checks:
    exists = col in df.columns
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {name}.{col}")

# Check pandas version
import pandas
print(f"\n[pandas version] {pandas.__version__}")

# Check if 'ME' freq works
try:
    sales['sale_date'] = pd.to_datetime(sales['sale_date'])
    test = sales.groupby(pd.Grouper(key='sale_date', freq='ME')).size()
    print("[OK] pd.Grouper freq='ME' works")
except Exception as e:
    print(f"[FAIL] pd.Grouper freq='ME' failed: {e}")
    print("       Will need to use freq='M' instead")

# Check inv_full merge columns
from pandas import merge
inventory_full = (
    inventory
    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']],
           left_on='product_id', right_on='id')
)
print(f"\n[inv_full merge] columns: {list(inventory_full.columns)}")

# Check the specific column NB05 uses: 'name_prod'
# The merge in NB05 uses suffixes=('_prod', '_cat')
# Let's check what NB05 actually gets
from pandas import read_csv
categories = read_csv(DATA_DIR / 'categories.csv')
warehouses = read_csv(DATA_DIR / 'warehouses.csv')

inv_full = (
    inventory
    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']],
           left_on='product_id', right_on='id')
    .merge(categories[['id', 'name']], left_on='category_id', right_on='id',
           suffixes=('_prod', '_cat'))
    .merge(warehouses[['id', 'name']], left_on='warehouse_id', right_on='id',
           suffixes=('_cat', '_wh'))
)
print(f"\n[inv_full after all merges] columns: {list(inv_full.columns)}")
print(f"  'name_prod' exists: {'name_prod' in inv_full.columns}")
print(f"  'name_cat' exists: {'name_cat' in inv_full.columns}")
print(f"  'name_wh' exists: {'name_wh' in inv_full.columns}")

# Check NB05 reorder_df columns
print("\n[NB05 reorder_df] columns expected:")
print("  product_id, sku, name_prod, quantity_on_hand, reorder_level, avg_daily_demand, days_of_stock_remaining")

# Check NB08 invoice KPI approach
print("\n[NB08] invoices.paid_amount check:")
print(f"  invoices.paid_amount exists: {'paid_amount' in invoices.columns}")
if 'paid_amount' in invoices.columns:
    print(f"  invoices.paid_amount sample: {invoices['paid_amount'].head(3).tolist()}")
print(f"  invoices.status unique: {invoices['status'].unique().tolist()}")

# Check NB09 rolling issue
sales_sorted = sales.sort_values(['company_id', 'sale_date'])
sales_sorted['sale_date'] = pd.to_datetime(sales_sorted['sale_date'])
print("\n[NB09] Rolling window test:")
try:
    result = (
        sales_sorted.groupby('company_id')['net_amount']
        .transform(lambda x: x.shift(1).rolling(28, min_periods=5).mean())
    )
    print("  Integer-based rolling(28): OK")
except Exception as e:
    print(f"  Integer-based rolling(28): FAILED - {e}")

print("\n=== PREFLIGHT COMPLETE ===")
