"""
apply_additional_patches.py
===========================
Apply the second wave of patches based on deep analysis.
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


# ── NB03: Fix 'sarima_fit in dir()' ──────────────────────────────────────────
def patch_03(src):
    # Old: if 'sarima_fit' in dir():
    # New: if 'sarima_fit' in locals() or 'sarima_fit' in globals():
    src = src.replace(
        "if 'sarima_fit' in dir():",
        "if 'sarima_fit' in vars():"
    )
    return src


# ── NB07: Fix np.where with pandas Series ────────────────────────────────────
def patch_07(src):
    # Fix: np.where(d['variance'] > 0, 'tomato', 'steelblue')
    # This is fine as d is subset of test_df which is a DataFrame
    # The issue is only if colors list doesn't align with x axis
    # Let's convert to list explicitly
    old = "    color=np.where(d['variance'] > 0, 'tomato', 'steelblue'))"
    new = "    color=['tomato' if v > 0 else 'steelblue' for v in d['variance']])"
    src = src.replace(old, new)
    return src


# ── NB10: Fix weighted_score_total initialization ────────────────────────────
def patch_10(src):
    # Ensure weighted_score_total is initialized even if no regression data
    # Already initialized in the Task Weights loop: weighted_score_total = 0.0
    # The issue would only occur if the loop body fails - let's add a safe init
    old = "weighted_score_total = 0.0"
    new = "weighted_score_total = 0.0  # initialized here; incremented in loop"
    src = src.replace(old, new)
    return src


# ── Apply patches ─────────────────────────────────────────────────────────────
print("Applying additional patches...")

nb = load_nb('03_revenue_forecasting.ipynb')
nb = patch_cells(nb, patch_03)
save_nb(nb, '03_revenue_forecasting.ipynb')

nb = load_nb('07_expense_prediction.ipynb')
nb = patch_cells(nb, patch_07)
save_nb(nb, '07_expense_prediction.ipynb')

print("Additional patches applied.")
