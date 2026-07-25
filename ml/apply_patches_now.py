"""
apply_patches_now.py
====================
Apply all notebook patches immediately (without executing).
This pre-fixes the notebooks so they're ready to run.
"""

import json
import re
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
            src = patch_fn(src)
            # Re-split into lines (keep as list of strings for notebook format)
            lines = src.split('\n')
            cell['source'] = [l + '\n' for l in lines[:-1]] + [lines[-1]] if lines else []
    return nb


# ─────────────────────────────────────────────────────────────────────────────
# Universal patch: pickle → joblib
# ─────────────────────────────────────────────────────────────────────────────

def universal(src):
    # Replace pickle import
    src = src.replace('import pickle', 'import joblib')

    # Replace pickle.dump/load
    src = src.replace('pickle.dump(', 'joblib.dump(')
    src = src.replace('pickle.load(', 'joblib.load(')

    # Fix joblib.dump inside 'with open(..., "wb") as f:' blocks
    # Pattern: rewrite `with open(path, 'wb') as f:\n    joblib.dump(obj, f)` 
    #       to `joblib.dump(obj, path)`
    lines = src.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect 'with open(' ... "'wb'" ... 'as f:'
        if re.match(r'\s*with open\(', line) and ("'wb'" in line or '"wb"' in line) and 'as f:' in line:
            indent = len(line) - len(line.lstrip())
            inner_indent = indent + 4

            # Extract path expression
            m = re.search(r'with open\((.+?),\s*[\'"]wb[\'"]\)\s+as\s+f:', line)
            path_expr = m.group(1).strip() if m else None

            # Gather body lines
            j = i + 1
            body = []
            while j < len(lines) and (len(lines[j]) - len(lines[j].lstrip()) >= inner_indent or not lines[j].strip()):
                if lines[j].strip():
                    body.append(lines[j])
                j += 1

            # Check if body has joblib.dump(obj, f)
            replaced = False
            if path_expr:
                for bl in body:
                    bl_s = bl.strip()
                    if bl_s.startswith('joblib.dump(') and bl_s.endswith(', f)'):
                        obj_expr = bl_s[len('joblib.dump('):-len(', f)')]
                        sp = ' ' * indent
                        result.append(f'{sp}joblib.dump({obj_expr}, {path_expr})')
                        replaced = True
                        break
                    elif bl_s.startswith('joblib.dump(') and ', f)' not in bl_s:
                        # handle multi-line dump or dict arg
                        # Just keep as-is but in the with block form
                        pass

            if replaced:
                i = j
                continue
            else:
                # Keep original with block
                result.append(line)
                i += 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


# ─────────────────────────────────────────────────────────────────────────────
# NB02: Data Preprocessing
# ─────────────────────────────────────────────────────────────────────────────

def patch_02(src):
    src = universal(src)
    # gross_amount → total_amount
    src = src.replace(
        "[c for c in ['gross_amount', 'discount_amount', 'net_amount']",
        "[c for c in ['total_amount', 'discount_amount', 'net_amount']"
    )
    return src


# ─────────────────────────────────────────────────────────────────────────────
# NB05: Inventory Prediction
# ─────────────────────────────────────────────────────────────────────────────

def patch_05(src):
    src = universal(src)
    # Warehouse name after merge is 'name' not 'name_wh' — add rename
    old = (
        "    .merge(warehouses[['id', 'name']], left_on='warehouse_id', right_on='id',\n"
        "           suffixes=('_cat', '_wh'))\n"
        ")"
    )
    new = (
        "    .merge(warehouses[['id', 'name']], left_on='warehouse_id', right_on='id',\n"
        "           suffixes=('_cat', '_wh'))\n"
        "    .rename(columns={'name': 'name_wh'})\n"
        ")"
    )
    src = src.replace(old, new)
    return src


# ─────────────────────────────────────────────────────────────────────────────
# NB07: Expense Prediction
# ─────────────────────────────────────────────────────────────────────────────

def patch_07(src):
    src = universal(src)
    # groupby.apply include_groups fix (pandas 2.x)
    src = src.replace(
        "    .apply(lambda g: pd.Series({\n"
        "        'RMSE': np.sqrt(mean_squared_error(g['total_expense'], g['xgb_pred'])),\n"
        "        'MAPE_%': mape(g['total_expense'].values, g['xgb_pred'].values)\n"
        "    }))\n",
        "    .apply(lambda g: pd.Series({\n"
        "        'RMSE': np.sqrt(mean_squared_error(g['total_expense'], g['xgb_pred'])),\n"
        "        'MAPE_%': mape(g['total_expense'].values, g['xgb_pred'].values)\n"
        "    }), include_groups=False)\n"
    )
    return src


# ─────────────────────────────────────────────────────────────────────────────
# NB08: Business Health Score
# ─────────────────────────────────────────────────────────────────────────────

def patch_08(src):
    src = universal(src)
    # Replace broken lambda with paid_amount sum
    src = src.replace(
        "        paid_invoiced  = ('total_amount', lambda x: x[invoices.loc[x.index, 'status'] == 'paid'].sum()),",
        "        paid_invoiced  = ('paid_amount', 'sum'),"
    )
    return src


# ─────────────────────────────────────────────────────────────────────────────
# NB09: Anomaly Detection
# ─────────────────────────────────────────────────────────────────────────────

def patch_09(src):
    src = universal(src)
    # rolling('28D') → rolling(28)
    src = src.replace(
        ".transform(lambda x: x.shift(1).rolling('28D', min_periods=5).mean())",
        ".transform(lambda x: x.shift(1).rolling(28, min_periods=5).mean())"
    )
    src = src.replace(
        ".transform(lambda x: x.shift(1).rolling('28D', min_periods=5).std())",
        ".transform(lambda x: x.shift(1).rolling(28, min_periods=5).std())"
    )
    return src


# ─────────────────────────────────────────────────────────────────────────────
# NB10: Model Comparison
# ─────────────────────────────────────────────────────────────────────────────

def patch_10(src):
    src = universal(src)
    # Fix Python 3.10 incompatible f-string nested braces
    # f'{'Task':<30} {'Best Model':<25} {'MAPE_%':>8}  {'Impact Weight':>14}'
    src = src.replace(
        "print(f'{'Task':<30} {'Best Model':<25} {'MAPE_%':>8}  {'Impact Weight':>14}')",
        "print('{:<30} {:<25} {:>8}  {:>14}'.format('Task', 'Best Model', 'MAPE_%', 'Impact Weight'))"
    )
    return src


# ─────────────────────────────────────────────────────────────────────────────
# Apply all patches
# ─────────────────────────────────────────────────────────────────────────────

patches = {
    '01_data_exploration.ipynb':    universal,
    '02_data_preprocessing.ipynb':  patch_02,
    '03_revenue_forecasting.ipynb': universal,
    '04_sales_forecasting.ipynb':   universal,
    '05_inventory_prediction.ipynb':patch_05,
    '06_profit_prediction.ipynb':   universal,
    '07_expense_prediction.ipynb':  patch_07,
    '08_business_health_score.ipynb':patch_08,
    '09_anomaly_detection.ipynb':   patch_09,
    '10_model_comparison.ipynb':    patch_10,
}

print("Applying patches to notebooks...")
for nb_name, patch_fn in patches.items():
    nb = load_nb(nb_name)
    nb = patch_cells(nb, patch_fn)
    save_nb(nb, nb_name)

print("\nAll patches applied.")
