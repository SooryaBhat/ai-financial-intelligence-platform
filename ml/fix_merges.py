"""
fix_merges.py
=============
Fix MergeError: duplicate columns in merges due to pandas 2.x strict behavior.
Applies to NB02 and NB04.
"""

import json
from pathlib import Path

nb_dir = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks')


def load_nb(name):
    with open(nb_dir / name, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_nb(nb, name):
    with open(nb_dir / name, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"  Saved: {name}")

def patch_cells(nb, patch_fn):
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            src = ''.join(cell['source'])
            new_src = patch_fn(src)
            lines = new_src.split('\n')
            cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    return nb


def fix_nb02_merges(src):
    """Fix duplicate column 'id_prod' in NB02 prod_sales merge chain."""
    # The issue: after merging with products using suffixes=('', '_prod'),
    # we get 'id_prod' (from products.id). Then merging categories with
    # suffixes=('_prod', '_cat') tries to create 'id_prod' again.
    # Fix: After products merge, drop the redundant 'id' column from products
    # before the categories merge; OR just select non-id columns from categories.
    
    # Original:
    # .merge(categories[['id', 'name']], left_on='category_id', right_on='id',
    #        suffixes=('_prod', '_cat'))
    # Fix: Don't use categories 'id' at all for the merge key result
    # Use left_on/right_on and then immediately drop the right 'id'
    
    old_cat_merge = (
        "    .merge(categories[['id', 'name']], left_on='category_id', right_on='id',\n"
        "           suffixes=('_prod', '_cat'))"
    )
    new_cat_merge = (
        "    .merge(categories[['id', 'name']].rename(columns={'id': 'cat_id', 'name': 'name_cat'}),\n"
        "           left_on='category_id', right_on='cat_id')\n"
        "    .drop(columns=['cat_id'])"
    )
    src = src.replace(old_cat_merge, new_cat_merge)
    
    # Fix any downstream references to 'name_cat' (was already 'name_cat' from suffixes approach)
    # The suffixes=('_prod', '_cat') would have produced name_prod and name_cat
    # Our rename produces name_cat directly - no change needed
    
    return src


def fix_nb04_merges(src):
    """Fix duplicate column 'id_prod' in NB04 items_full merge chain."""
    # Same pattern as NB02:
    # sale_items
    # .merge(sales[...], left_on='sale_id', right_on='id', suffixes=('', '_sale'))
    # .merge(products[...], left_on='product_id', right_on='id', suffixes=('', '_prod'))
    # .merge(categories[['id', 'name']], left_on='category_id', right_on='id',
    #        suffixes=('_prod', '_cat'))
    # After products merge we have 'id_prod'. Then categories merge tries to create 'id_prod' again.
    
    old_cat = (
        "    .merge(categories[['id', 'name']], left_on='category_id', right_on='id',\n"
        "           suffixes=('_prod', '_cat'))"
    )
    new_cat = (
        "    .merge(categories[['id', 'name']].rename(columns={'id': 'cat_id', 'name': 'name_cat'}),\n"
        "           left_on='category_id', right_on='cat_id')\n"
        "    .drop(columns=['cat_id'])"
    )
    src = src.replace(old_cat, new_cat)
    
    # Fix any references to 'name_cat' in NB04 (already used that name in the code)
    # The aggregation uses 'name_cat' which is now directly available 
    
    return src


print("Fixing merge errors in NB02 and NB04...")

nb = load_nb('02_data_preprocessing.ipynb')
nb = patch_cells(nb, fix_nb02_merges)
save_nb(nb, '02_data_preprocessing.ipynb')

nb = load_nb('04_sales_forecasting.ipynb')
nb = patch_cells(nb, fix_nb04_merges)
save_nb(nb, '04_sales_forecasting.ipynb')

print("Merge fixes applied.")
