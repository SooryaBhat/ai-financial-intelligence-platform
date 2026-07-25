"""
update_nb03_r2.py
=================
Format R2, RMSE, MAE, MAPE cleanly in 03_revenue_forecasting.ipynb Cell 11 & Cell 13.
"""
import json
from pathlib import Path

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])

        # Cell 11 eval_metrics return structure
        if 'def eval_metrics(y_true, y_pred, model_name):' in src:
            old_code = (
                "def eval_metrics(y_true, y_pred, model_name):\n"
                "    rmse = np.sqrt(mean_squared_error(y_true, y_pred))\n"
                "    mae  = mean_absolute_error(y_true, y_pred)\n"
                "    mape_val = mape(y_true, y_pred)\n"
                "    r2 = r2_score(y_true, y_pred)\n"
                "    print(f'{model_name:<24}  RMSE={rmse:>12,.0f}  MAE={mae:>12,.0f}  MAPE={mape_val:>6.2f}%  R²={r2:>6.3f}')\n"
                "    return {'model': model_name, 'RMSE': rmse, 'MAE': mae, 'MAPE': mape_val, 'R2': r2}"
            )
            new_code = (
                "def eval_metrics(y_true, y_pred, model_name):\n"
                "    rmse = np.sqrt(mean_squared_error(y_true, y_pred))\n"
                "    mae  = mean_absolute_error(y_true, y_pred)\n"
                "    mape_val = mape(y_true, y_pred)\n"
                "    r2 = r2_score(y_true, y_pred)\n"
                "    print(f'{model_name:<24}  RMSE={rmse:>12,.0f}  MAE={mae:>12,.0f}  MAPE={mape_val:>6.2f}%  R²={r2:>6.3f}')\n"
                "    return {'model': model_name, 'RMSE': round(rmse, 2), 'MAE': round(mae, 2), 'MAPE_%': round(mape_val, 2), 'R2': round(r2, 4)}"
            )
            src = src.replace(old_code, new_code)

        # Cell 13 results_df sorting
        if "results_df = pd.DataFrame(results).sort_values('MAPE')" in src:
            src = src.replace(
                "results_df = pd.DataFrame(results).sort_values('MAPE')",
                "results_df = pd.DataFrame(results).sort_values('MAPE_%')"
            )

        lines = src.split('\n')
        cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("NB03 R2 metrics formatting updated.")
