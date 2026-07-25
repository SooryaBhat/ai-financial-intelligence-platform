"""
fix_remaining_failures.py
=========================
Fix the specific root causes for NB04, NB08, and NB09.
"""

import json
from pathlib import Path

NOTEBOOKS_DIR = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks')

def load_nb(name):
    with open(NOTEBOOKS_DIR / name, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_nb(nb, name):
    with open(NOTEBOOKS_DIR / name, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"  Saved: {name}")

def patch_cells(nb, patch_fn):
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            src = ''.join(cell['source'])
            new_src = patch_fn(src)
            if new_src != src:
                lines = new_src.split('\n')
                cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    return nb

# ── NB04 Fix ───────────
def fix_nb04(src):
    # products merge must explicitly rename name -> name_prod
    old_code = (
        "items_full = (\n"
        "    sale_items\n"
        "    .merge(sales[['id', 'sale_date', 'company_id', 'branch_id']],\n"
        "           left_on='sale_id', right_on='id', suffixes=('', '_sale'))\n"
        "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']],\n"
        "           left_on='product_id', right_on='id', suffixes=('', '_prod'))\n"
        "    .merge(categories[['id', 'name']].rename(columns={'id': 'cat_id', 'name': 'name_cat'}),\n"
        "           left_on='category_id', right_on='cat_id')\n"
        "    .drop(columns=['cat_id'])\n"
        ")"
    )
    if old_code not in src:
        # Check standard format
        old_code = (
            "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']],\n"
            "           left_on='product_id', right_on='id', suffixes=('', '_prod'))"
        )
        new_code = (
            "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']].rename(columns={'name': 'name_prod'}),\n"
            "           left_on='product_id', right_on='id')"
        )
        src = src.replace(old_code, new_code)
    else:
        new_code = (
            "items_full = (\n"
            "    sale_items\n"
            "    .merge(sales[['id', 'sale_date', 'company_id', 'branch_id']],\n"
            "           left_on='sale_id', right_on='id')\n"
            "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']].rename(columns={'name': 'name_prod'}),\n"
            "           left_on='product_id', right_on='id')\n"
            "    .merge(categories[['id', 'name']].rename(columns={'id': 'cat_id', 'name': 'name_cat'}),\n"
            "           left_on='category_id', right_on='cat_id')\n"
            "    .drop(columns=['cat_id'], errors='ignore')\n"
            ")"
        )
        src = src.replace(old_code, new_code)
    return src

# ── NB08 Fix ───────────
def fix_nb08(src):
    # products[['id', 'cost_price']] must include 'company_id'
    old_code = ".merge(products[['id', 'cost_price']], left_on='product_id', right_on='id')"
    new_code = ".merge(products[['id', 'company_id', 'cost_price']], left_on='product_id', right_on='id')"
    src = src.replace(old_code, new_code)
    return src

# ── NB09 Fix ───────────
def fix_nb09(src):
    # Avoid duplicate 'net_amount' in column selection
    old_code = "anomaly_df = sales_sorted[ANOMALY_FEATURES + ['id', 'sale_date', 'company_id', 'net_amount']].copy()"
    new_code = "anomaly_df = sales_sorted[list(dict.fromkeys(ANOMALY_FEATURES + ['id', 'sale_date', 'company_id', 'net_amount']))].copy()"
    src = src.replace(old_code, new_code)
    return src

print("Fixing NB04, NB08, and NB09...")

nb4 = patch_cells(load_nb('04_sales_forecasting.ipynb'), fix_nb04)
save_nb(nb4, '04_sales_forecasting.ipynb')

nb8 = patch_cells(load_nb('08_business_health_score.ipynb'), fix_nb08)
save_nb(nb8, '08_business_health_score.ipynb')

nb9 = patch_cells(load_nb('09_anomaly_detection.ipynb'), fix_nb09)
save_nb(nb9, '09_anomaly_detection.ipynb')

print("Fixes applied.")
