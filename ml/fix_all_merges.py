"""
fix_all_merges.py
=================
Fix all pandas merge suffix collisions across notebooks 01-10.
Uses explicit column renamers prior to merging to prevent pandas 2.3 MergeError.
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

# ── NB01 ───────────
def patch_nb01(src):
    # Fix exp_full merge
    old_exp = (
        "exp_full = (\n"
        "    expenses\n"
        "    .merge(branches[['id', 'name', 'city']], left_on='branch_id', right_on='id',\n"
        "           suffixes=('', '_branch'))\n"
        "    .merge(companies[['id', 'name']], left_on='company_id', right_on='id',\n"
        "           suffixes=('_branch', '_co'))\n"
        ")"
    )
    new_exp = (
        "exp_full = (\n"
        "    expenses\n"
        "    .merge(branches[['id', 'name', 'city']].rename(columns={'name': 'name_branch', 'city': 'city_branch'}), left_on='branch_id', right_on='id')\n"
        "    .merge(companies[['id', 'name']].rename(columns={'name': 'name_co'}), left_on='company_id', right_on='id')\n"
        ")"
    )
    src = src.replace(old_exp, new_exp)

    # Fix sales_items_full merge
    old_items = (
        "sales_items_full = (\n"
        "    sale_items\n"
        "    .merge(sales[['id', 'sale_date', 'company_id', 'branch_id']], left_on='sale_id', right_on='id')\n"
        "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price', 'selling_price']], left_on='product_id', right_on='id')\n"
        "    .merge(categories[['id', 'name']], left_on='category_id', right_on='id',\n"
        "           suffixes=('_prod', '_cat'))\n"
        ")"
    )
    new_items = (
        "sales_items_full = (\n"
        "    sale_items\n"
        "    .merge(sales[['id', 'sale_date', 'company_id', 'branch_id']], left_on='sale_id', right_on='id')\n"
        "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price', 'selling_price']].rename(columns={'name': 'name_prod'}), left_on='product_id', right_on='id')\n"
        "    .merge(categories[['id', 'name']].rename(columns={'name': 'name_cat'}), left_on='category_id', right_on='id')\n"
        ")"
    )
    src = src.replace(old_items, new_items)

    return src

# ── NB05 ───────────
def patch_nb05(src):
    old_inv = (
        "inv_full = (\n"
        "    inventory\n"
        "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']],\n"
        "           left_on='product_id', right_on='id')\n"
        "    .merge(categories[['id', 'name']], left_on='category_id', right_on='id',\n"
        "           suffixes=('_prod', '_cat'))\n"
        "    .merge(warehouses[['id', 'name']], left_on='warehouse_id', right_on='id',\n"
        "           suffixes=('_cat', '_wh'))\n"
        "    .rename(columns={'name': 'name_wh'})\n"
        ")"
    )
    if old_inv not in src:
        old_inv = (
            "inv_full = (\n"
            "    inventory\n"
            "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']],\n"
            "           left_on='product_id', right_on='id')\n"
            "    .merge(categories[['id', 'name']], left_on='category_id', right_on='id',\n"
            "           suffixes=('_prod', '_cat'))\n"
            "    .merge(warehouses[['id', 'name']], left_on='warehouse_id', right_on='id',\n"
            "           suffixes=('_cat', '_wh'))\n"
            ")"
        )
    new_inv = (
        "inv_full = (\n"
        "    inventory\n"
        "    .merge(products[['id', 'name', 'sku', 'category_id', 'cost_price']].rename(columns={'name': 'name_prod'}), left_on='product_id', right_on='id')\n"
        "    .merge(categories[['id', 'name']].rename(columns={'name': 'name_cat'}), left_on='category_id', right_on='id')\n"
        "    .merge(warehouses[['id', 'name']].rename(columns={'name': 'name_wh'}), left_on='warehouse_id', right_on='id')\n"
        ")"
    )
    src = src.replace(old_inv, new_inv)
    return src

# ── NB06 ───────────
def patch_nb06(src):
    old_cost = (
        "items_cost = (\n"
        "    sale_items\n"
        "    .merge(products[['id', 'cost_price', 'category_id']],\n"
        "           left_on='product_id', right_on='id', suffixes=('', '_prod'))\n"
        "    .merge(sales[['id', 'sale_date', 'company_id', 'branch_id']],\n"
        "           left_on='sale_id', right_on='id', suffixes=('', '_sale'))\n"
        ")"
    )
    new_cost = (
        "items_cost = (\n"
        "    sale_items\n"
        "    .merge(products[['id', 'cost_price', 'category_id']], left_on='product_id', right_on='id')\n"
        "    .merge(sales[['id', 'sale_date', 'company_id', 'branch_id']], left_on='sale_id', right_on='id')\n"
        ")"
    )
    src = src.replace(old_cost, new_cost)
    return src

# ── NB07 ───────────
def patch_nb07(src):
    old_exp = (
        "exp_full = (\n"
        "    expenses\n"
        "    .merge(branches[['id', 'name', 'city']], left_on='branch_id', right_on='id',\n"
        "           suffixes=('', '_branch'))\n"
        "    .merge(companies[['id', 'name']], left_on='company_id', right_on='id',\n"
        "           suffixes=('_branch', '_co'))\n"
        ")"
    )
    new_exp = (
        "exp_full = (\n"
        "    expenses\n"
        "    .merge(branches[['id', 'name', 'city']].rename(columns={'name': 'name_branch', 'city': 'city_branch'}), left_on='branch_id', right_on='id')\n"
        "    .merge(companies[['id', 'name']].rename(columns={'name': 'name_co'}), left_on='company_id', right_on='id')\n"
        ")"
    )
    src = src.replace(old_exp, new_exp)
    return src

# ── NB08 ───────────
def patch_nb08(src):
    old_cost = (
        "items_cost = (\n"
        "    sale_items\n"
        "    .merge(products[['id', 'cost_price']], left_on='product_id', right_on='id')\n"
        "    .merge(sales[['id', 'sale_date', 'company_id']], left_on='sale_id', right_on='id',\n"
        "           suffixes=('_item', '_sale'))\n"
        ")"
    )
    new_cost = (
        "items_cost = (\n"
        "    sale_items\n"
        "    .merge(products[['id', 'cost_price']], left_on='product_id', right_on='id')\n"
        "    .merge(sales[['id', 'sale_date', 'company_id']], left_on='sale_id', right_on='id')\n"
        ")"
    )
    src = src.replace(old_cost, new_cost)
    return src

# Apply all patches
print("Applying comprehensive merge fixes...")
nb1 = patch_cells(load_nb('01_data_exploration.ipynb'), patch_nb01)
save_nb(nb1, '01_data_exploration.ipynb')

nb5 = patch_cells(load_nb('05_inventory_prediction.ipynb'), patch_nb05)
save_nb(nb5, '05_inventory_prediction.ipynb')

nb6 = patch_cells(load_nb('06_profit_prediction.ipynb'), patch_nb06)
save_nb(nb6, '06_profit_prediction.ipynb')

nb7 = patch_cells(load_nb('07_expense_prediction.ipynb'), patch_nb07)
save_nb(nb7, '07_expense_prediction.ipynb')

nb8 = patch_cells(load_nb('08_business_health_score.ipynb'), patch_nb08)
save_nb(nb8, '08_business_health_score.ipynb')

print("All merge fixes completed.")
