"""
run_ml_pipeline.py
==================
Master script to fix, validate, and run all 10 ML notebooks for the
AI Financial Intelligence Platform.

Usage:
    python run_ml_pipeline.py

What it does:
    1. Creates required directories (models/, reports/)
    2. Patches each notebook to fix known issues
    3. Executes each notebook via nbformat/nbconvert
    4. Reports success/failure and errors
"""

import os
import sys
import json
import copy
import traceback
from pathlib import Path

import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
from nbconvert.preprocessors import ExecutePreprocessor

# ── Paths ─────────────────────────────────────────────────────────────────────
ML_DIR       = Path(__file__).resolve().parent
NOTEBOOKS_DIR = ML_DIR / 'notebooks'
MODELS_DIR   = ML_DIR / 'models'
REPORTS_DIR  = ML_DIR / 'reports'

MODELS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

NOTEBOOKS = [
    '01_data_exploration.ipynb',
    '02_data_preprocessing.ipynb',
    '03_revenue_forecasting.ipynb',
    '04_sales_forecasting.ipynb',
    '05_inventory_prediction.ipynb',
    '06_profit_prediction.ipynb',
    '07_expense_prediction.ipynb',
    '08_business_health_score.ipynb',
    '09_anomaly_detection.ipynb',
    '10_model_comparison.ipynb',
]

# ── Patch functions ────────────────────────────────────────────────────────────

def patch_source(src: str, nb_name: str) -> str:
    """Apply source-level patches to notebook cell source code."""

    # ── Universal fixes ────────────────────────────────────────────────────────

    # 1. Replace pickle with joblib for model saving
    if 'import pickle' in src:
        src = src.replace('import pickle', 'import joblib')
    if 'with open(' in src and "pickle.dump" in src:
        # Replace pickle.dump patterns for model saving
        import re
        # Pattern: with open(path, 'wb') as f:\n    pickle.dump(obj, f)
        # Replace with: joblib.dump(obj, path)
        # We handle this by injecting joblib at top and replacing dump/load
        src = src.replace('pickle.dump(', 'joblib.dump(')
        src = src.replace('pickle.load(', 'joblib.load(')
        # Fix joblib.dump signature: joblib.dump(obj, f) -> joblib.dump(obj, path)
        # For lines inside 'with open' blocks, we need to restructure
    if 'pickle.dump(' in src:
        src = src.replace('pickle.dump(', 'joblib.dump(')
    if 'pickle.load(' in src:
        src = src.replace('pickle.load(', 'joblib.load(')

    # 2. Fix .pkl extensions -> .pkl (keep joblib compatible)
    # joblib can save to .pkl files fine

    # 3. Fix pandas 'ME' frequency alias (use 'ME' which is valid in pandas >= 2.2)
    # If using older pandas, 'M' is needed. We'll detect and handle in the notebook.
    # For safety: keep 'ME' which is the newer standard

    # 4. Fix f-string issues for Python < 3.12
    # Python 3.10 doesn't allow nested quotes in f-strings the same way
    # Fix the specific case in NB10
    if nb_name == '10_model_comparison.ipynb':
        # Fix: f'{'Task':<30}' → use format() or variables
        src = src.replace(
            "print(f'{'Task':<30} {'Best Model':<25} {'MAPE_%':>8}  {'Impact Weight':>14}')",
            "print(f\"{'Task':<30} {'Best Model':<25} {'MAPE_%':>8}  {'Impact Weight':>14}\")"
        )

    # ── NB02 specific fixes ────────────────────────────────────────────────────
    if nb_name == '02_data_preprocessing.ipynb':
        # 'gross_amount' doesn't exist in sales, use 'total_amount' instead
        src = src.replace(
            "sales_numeric_cols = [c for c in ['gross_amount', 'discount_amount', 'net_amount']",
            "sales_numeric_cols = [c for c in ['total_amount', 'discount_amount', 'net_amount']"
        )

    # ── NB05 specific fixes ────────────────────────────────────────────────────
    if nb_name == '05_inventory_prediction.ipynb':
        # Fix potential column name issue: 'name_prod' might not exist after merge
        # The merge creates 'name_prod' and 'name_cat' - let's verify the reorder_df columns
        # The reorder_df uses 'name_prod' which should come from inv_consumption
        # inv_consumption comes from inv_full which was merged with products as 'name'
        # After merge with suffixes=('_prod', '_cat'), product name becomes 'name_prod'
        # This should be fine, but add a fallback
        pass

    # ── NB07 specific fixes ────────────────────────────────────────────────────
    if nb_name == '07_expense_prediction.ipynb':
        # Fix pandas groupby().apply() deprecation for include_groups
        src = src.replace(
            ".apply(lambda g: pd.Series({\n        'RMSE': np.sqrt(mean_squared_error(g['total_expense'], g['xgb_pred'])),\n        'MAPE_%': mape(g['total_expense'].values, g['xgb_pred'].values)\n    }))",
            ".apply(lambda g: pd.Series({\n        'RMSE': np.sqrt(mean_squared_error(g['total_expense'], g['xgb_pred'])),\n        'MAPE_%': mape(g['total_expense'].values, g['xgb_pred'].values)\n    }), include_groups=False)"
        )

    # ── NB08 specific fixes ────────────────────────────────────────────────────
    if nb_name == '08_business_health_score.ipynb':
        # Fix the lambda in groupby.agg that references outer scope 'invoices'
        # The lambda `lambda x: x[invoices.loc[x.index, 'status'] == 'paid'].sum()`
        # will fail because 'invoices' is being redefined in scope issues
        # Replace with a simpler approach
        old_kpi5 = (
            "    paid_invoiced  = ('total_amount', lambda x: x[invoices.loc[x.index, 'status'] == 'paid'].sum()),"
        )
        new_kpi5 = (
            "    paid_invoiced  = ('paid_amount', 'sum'),"
        )
        src = src.replace(old_kpi5, new_kpi5)

    # ── NB09 specific fixes ────────────────────────────────────────────────────
    if nb_name == '09_anomaly_detection.ipynb':
        # Fix rolling('28D') - requires DatetimeIndex, not just a datetime column
        # Replace time-based rolling window with integer-based rolling window
        src = src.replace(
            ".transform(lambda x: x.shift(1).rolling('28D', min_periods=5).mean())",
            ".transform(lambda x: x.shift(1).rolling(28, min_periods=5).mean())"
        )
        src = src.replace(
            ".transform(lambda x: x.shift(1).rolling('28D', min_periods=5).std())",
            ".transform(lambda x: x.shift(1).rolling(28, min_periods=5).std())"
        )

    return src


def load_notebook(path: Path) -> dict:
    """Load a Jupyter notebook from file."""
    with open(path, 'r', encoding='utf-8') as f:
        return nbformat.read(f, as_version=4)


def save_notebook(nb: dict, path: Path) -> None:
    """Save a Jupyter notebook to file."""
    with open(path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)


def patch_notebook(nb_name: str) -> Path:
    """Load, patch, and save a notebook. Returns path to patched notebook."""
    nb_path = NOTEBOOKS_DIR / nb_name
    nb = load_notebook(nb_path)

    # Patch each code cell
    for cell in nb.cells:
        if cell.cell_type == 'code':
            original = cell.source
            patched = patch_source(original, nb_name)
            cell.source = patched

    # Save patched notebook (overwrite in place)
    save_notebook(nb, nb_path)
    return nb_path


def run_notebook(nb_path: Path, timeout: int = 600) -> tuple:
    """
    Execute a Jupyter notebook.

    Returns:
        (success: bool, error_msg: str)
    """
    nb = load_notebook(nb_path)

    ep = ExecutePreprocessor(
        timeout=timeout,
        kernel_name='python3',
        allow_errors=False,
    )

    try:
        print(f"  Executing {nb_path.name}...", flush=True)
        ep.preprocess(nb, {'metadata': {'path': str(NOTEBOOKS_DIR)}})
        # Save executed notebook (with outputs)
        save_notebook(nb, nb_path)
        return True, ''
    except Exception as e:
        tb = traceback.format_exc()
        # Save partially executed notebook anyway
        try:
            save_notebook(nb, nb_path)
        except Exception:
            pass
        return False, str(tb)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("  AI Financial Intelligence Platform — ML Pipeline Runner")
    print("=" * 70)
    print(f"  Notebooks: {NOTEBOOKS_DIR}")
    print(f"  Models:    {MODELS_DIR}")
    print(f"  Reports:   {REPORTS_DIR}")
    print()

    results = []

    for nb_name in NOTEBOOKS:
        print(f"\n{'─'*70}")
        print(f"  Processing: {nb_name}")
        print(f"{'─'*70}")

        nb_path = NOTEBOOKS_DIR / nb_name
        if not nb_path.exists():
            print(f"  ERROR: Notebook not found: {nb_path}")
            results.append({'notebook': nb_name, 'status': 'NOT_FOUND', 'error': 'File not found'})
            continue

        # Step 1: Patch notebook
        print(f"  [1/2] Patching notebook...")
        try:
            patch_notebook(nb_name)
            print(f"        Patch applied successfully.")
        except Exception as e:
            print(f"        PATCH ERROR: {e}")
            results.append({'notebook': nb_name, 'status': 'PATCH_ERROR', 'error': str(e)})
            continue

        # Step 2: Execute notebook
        print(f"  [2/2] Executing notebook (timeout=600s)...")
        success, error = run_notebook(nb_path)

        if success:
            print(f"        SUCCESS: {nb_name} executed cleanly.")
            results.append({'notebook': nb_name, 'status': 'SUCCESS', 'error': ''})
        else:
            # Extract the key error message
            error_lines = error.strip().split('\n')
            key_error = '\n'.join(error_lines[-10:])  # last 10 lines
            print(f"        FAILED:")
            print(key_error)
            results.append({'notebook': nb_name, 'status': 'FAILED', 'error': key_error})

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    for r in results:
        icon = "✓" if r['status'] == 'SUCCESS' else "✗"
        print(f"  {icon} {r['notebook']:<40}  {r['status']}")

    successful = [r for r in results if r['status'] == 'SUCCESS']
    failed     = [r for r in results if r['status'] == 'FAILED']

    print()
    print(f"  Total:     {len(results)}")
    print(f"  Succeeded: {len(successful)}")
    print(f"  Failed:    {len(failed)}")

    # Save summary JSON
    summary_path = REPORTS_DIR / 'pipeline_execution_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Summary saved: {summary_path}")

    if failed:
        print("\n  FAILURES:")
        for r in failed:
            print(f"\n  [{r['notebook']}]")
            print(r['error'][:500])

    return len(failed) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
