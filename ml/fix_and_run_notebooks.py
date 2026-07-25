"""
fix_and_run_notebooks.py
========================
Master script to patch, validate, and run all 10 ML notebooks for the
AI Financial Intelligence Platform.

Usage:
    python fix_and_run_notebooks.py
"""

import os
import sys
import json
import traceback
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

# ── Paths ─────────────────────────────────────────────────────────────────────
ML_DIR        = Path(__file__).resolve().parent
NOTEBOOKS_DIR = ML_DIR / 'notebooks'
MODELS_DIR    = ML_DIR / 'models'
REPORTS_DIR   = ML_DIR / 'reports'

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


# ─────────────────────────────────────────────────────────────────────────────
# Cell-level patch functions
# ─────────────────────────────────────────────────────────────────────────────

def patch_cell_universal(src: str) -> str:
    """Universal patches for every notebook."""
    src = src.replace('import pickle', 'import joblib')
    src = src.replace('pickle.dump(', 'joblib.dump(')
    src = src.replace('pickle.load(', 'joblib.load(')
    return src


def patch_nb01(src: str) -> str:
    """NB01: Data Exploration fixes."""
    src = src.replace(
        "items_full.drop(columns=['id'])",
        "items_full.drop(columns=['id', 'id_x', 'id_y'], errors='ignore')"
    )
    old_exp = (
        "    .merge(branches[['id', 'name', 'city']], left_on='branch_id', right_on='id',\n"
        "           suffixes=('', '_branch'))\n"
        "    .merge(companies[['id', 'name']], left_on='company_id', right_on='id',\n"
        "           suffixes=('_branch', '_co'))"
    )
    new_exp = (
        "    .merge(branches[['id', 'name', 'city']].rename(columns={'name': 'name_branch', 'city': 'city_branch'}), left_on='branch_id', right_on='id')\n"
        "    .merge(companies[['id', 'name']].rename(columns={'name': 'name_co'}), left_on='company_id', right_on='id')"
    )
    src = src.replace(old_exp, new_exp)
    return src


def patch_nb02(src: str) -> str:
    """NB02: Data Preprocessing fixes."""
    src = src.replace(
        "[c for c in ['gross_amount', 'discount_amount', 'net_amount']",
        "[c for c in ['total_amount', 'discount_amount', 'net_amount']"
    )
    return src


def patch_nb03(src: str) -> str:
    """NB03: Revenue Forecasting fixes."""
    src = src.replace("if 'sarima_fit' in dir():", "if 'sarima_fit' in globals() or 'sarima_fit' in locals():")
    src = src.replace("if 'sarima_fit' in vars():", "if 'sarima_fit' in globals() or 'sarima_fit' in locals():")
    return src


def patch_nb04(src: str) -> str:
    """NB04: Sales Forecasting fixes."""
    src = src.replace(
        "products[['id', 'name', 'sku', 'category_id', 'cost_price']]",
        "products[['id', 'name', 'sku', 'category_id', 'cost_price']].rename(columns={'name': 'name_prod'})"
    )
    return src


def patch_nb05(src: str) -> str:
    """NB05: Inventory Prediction fixes."""
    return src


def patch_nb06(src: str) -> str:
    """NB06: Profit Prediction fixes."""
    return src


def patch_nb07(src: str) -> str:
    """NB07: Expense Prediction fixes."""
    src = src.replace(
        ".apply(lambda g: pd.Series({\n"
        "        'RMSE': np.sqrt(mean_squared_error(g['total_expense'], g['xgb_pred'])),\n"
        "        'MAPE_%': mape(g['total_expense'].values, g['xgb_pred'].values)\n"
        "    }))",
        ".apply(lambda g: pd.Series({\n"
        "        'RMSE': np.sqrt(mean_squared_error(g['total_expense'], g['xgb_pred'])),\n"
        "        'MAPE_%': mape(g['total_expense'].values, g['xgb_pred'].values)\n"
        "    }), include_groups=False)"
    )
    old_color = "    color=np.where(d['variance'] > 0, 'tomato', 'steelblue'))"
    new_color = "    color=['tomato' if v > 0 else 'steelblue' for v in d['variance']])"
    src = src.replace(old_color, new_color)
    return src


def patch_nb08(src: str) -> str:
    """NB08: Business Health Score fixes."""
    old_kpi5 = "paid_invoiced  = ('total_amount', lambda x: x[invoices.loc[x.index, 'status'] == 'paid'].sum()),"
    new_kpi5 = "paid_invoiced  = ('paid_amount', 'sum'),"
    src = src.replace(old_kpi5, new_kpi5)

    # In items_cost, products should not select company_id to avoid collision with sales.company_id
    src = src.replace(
        ".merge(products[['id', 'company_id', 'cost_price']], left_on='product_id', right_on='id')",
        ".merge(products[['id', 'cost_price']], left_on='product_id', right_on='id')"
    )

    # In inv_value, products MUST select company_id because inventory has no company_id
    old_inv = "inv_value = (\n    inventory\n    .merge(products[['id', 'cost_price']], left_on='product_id', right_on='id')"
    new_inv = "inv_value = (\n    inventory\n    .merge(products[['id', 'company_id', 'cost_price']], left_on='product_id', right_on='id')"
    src = src.replace(old_inv, new_inv)

    return src


def patch_nb09(src: str) -> str:
    """NB09: Anomaly Detection fixes."""
    src = src.replace(
        ".transform(lambda x: x.shift(1).rolling('28D', min_periods=5).mean())",
        ".transform(lambda x: x.shift(1).rolling(28, min_periods=5).mean())"
    )
    src = src.replace(
        ".transform(lambda x: x.shift(1).rolling('28D', min_periods=5).std())",
        ".transform(lambda x: x.shift(1).rolling(28, min_periods=5).std())"
    )
    src = src.replace(
        "anomaly_df = sales_sorted[ANOMALY_FEATURES + ['id', 'sale_date', 'company_id', 'net_amount']].copy()",
        "anomaly_df = sales_sorted[list(dict.fromkeys(ANOMALY_FEATURES + ['id', 'sale_date', 'company_id', 'net_amount']))].copy()"
    )
    return src


def patch_nb10(src: str) -> str:
    """NB10: Model Comparison fixes."""
    src = src.replace(
        "print(f'{'Task':<30} {'Best Model':<25} {'MAPE_%':>8}  {'Impact Weight':>14}')",
        "print('{:<30} {:<25} {:>8}  {:>14}'.format('Task', 'Best Model', 'MAPE_%', 'Impact Weight'))"
    )
    return src


PATCH_FUNCTIONS = {
    '01_data_exploration.ipynb':   patch_nb01,
    '02_data_preprocessing.ipynb': patch_nb02,
    '03_revenue_forecasting.ipynb':patch_nb03,
    '04_sales_forecasting.ipynb':  patch_nb04,
    '05_inventory_prediction.ipynb':patch_nb05,
    '06_profit_prediction.ipynb':  patch_nb06,
    '07_expense_prediction.ipynb': patch_nb07,
    '08_business_health_score.ipynb':patch_nb08,
    '09_anomaly_detection.ipynb':  patch_nb09,
    '10_model_comparison.ipynb':   patch_nb10,
}


def patch_notebook(nb_name: str) -> None:
    """Load, patch, and save notebook in-place."""
    path = NOTEBOOKS_DIR / nb_name

    with open(path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    specific_patcher = PATCH_FUNCTIONS.get(nb_name, lambda x: x)

    for cell in nb.cells:
        if cell.cell_type == 'code' and cell.source.strip():
            src = cell.source
            src = patch_cell_universal(src)
            src = specific_patcher(src)
            cell.source = src

    with open(path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

    print(f"    Patched: {nb_name}")


def run_notebook(nb_name: str, timeout: int = 900) -> tuple:
    """Execute a notebook. Returns (success, error_message)."""
    path = NOTEBOOKS_DIR / nb_name

    with open(path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(
        timeout=timeout,
        kernel_name='python3',
    )

    try:
        ep.preprocess(nb, {'metadata': {'path': str(NOTEBOOKS_DIR)}})
        with open(path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)
        return True, ''
    except Exception as exc:
        tb = traceback.format_exc()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)
        except Exception:
            pass
        return False, tb


def main():
    results = []

    print()
    print("=" * 70)
    print("  AI Financial Intelligence Platform -- ML Pipeline")
    print("  Fix + Execute All Notebooks")
    print("=" * 70)
    print(f"  Models dir:  {MODELS_DIR}")
    print(f"  Reports dir: {REPORTS_DIR}")
    print()

    for nb_name in NOTEBOOKS:
        print(f"\n{'-'*70}")
        print(f"  [{NOTEBOOKS.index(nb_name)+1}/{len(NOTEBOOKS)}] {nb_name}")
        print(f"{'-'*70}")

        nb_path = NOTEBOOKS_DIR / nb_name
        if not nb_path.exists():
            print(f"  ERROR: Not found: {nb_path}")
            results.append({'notebook': nb_name, 'status': 'NOT_FOUND', 'error': ''})
            continue

        print(f"  Applying patches...")
        try:
            patch_notebook(nb_name)
        except Exception as e:
            msg = f"Patch failed: {e}"
            print(f"  {msg}")
            results.append({'notebook': nb_name, 'status': 'PATCH_ERROR', 'error': msg})
            continue

        print(f"  Executing (timeout=900s)...", flush=True)
        success, error = run_notebook(nb_name)

        if success:
            print(f"  SUCCESS")
            results.append({'notebook': nb_name, 'status': 'SUCCESS', 'error': ''})
        else:
            lines = error.strip().split('\n')
            key_lines = []
            for j, ln in enumerate(lines):
                if 'Error' in ln or 'error' in ln or 'Exception' in ln:
                    key_lines = lines[max(0, j-2):min(len(lines), j+5)]
            if not key_lines:
                key_lines = lines[-15:]

            key_error = '\n'.join(key_lines)
            print(f"  FAILED:")
            print(key_error)
            results.append({'notebook': nb_name, 'status': 'FAILED', 'error': key_error})

    print()
    print("=" * 70)
    print("  PIPELINE SUMMARY")
    print("=" * 70)
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed_count  = sum(1 for r in results if r['status'] == 'FAILED')

    for r in results:
        icon = "OK" if r['status'] == 'SUCCESS' else "FAIL"
        print(f"  [{icon}] {r['notebook']}")

    print()
    print(f"  Succeeded: {success_count} / {len(results)}")
    print(f"  Failed:    {failed_count} / {len(results)}")

    print()
    print("  Saved Models:")
    for f in sorted(MODELS_DIR.glob("*.pkl")):
        sz = f.stat().st_size / 1024
        print(f"    {f.name:<55} ({sz:.1f} KB)")

    summary_path = REPORTS_DIR / 'pipeline_execution_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Summary: {summary_path}")

    return failed_count == 0


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
