"""
patch_nb03_clean.py
===================
Refine and perfect 03_revenue_forecasting.ipynb:
1. Add r2_score to sklearn imports and eval_metrics function.
2. Ensure eval_metrics calculates RMSE, MAE, MAPE, and R2.
3. Fix date frequency in 6-month future forecast (using pd.date_range with freq='ME').
4. Safely check sarima_fit in globals()/locals().
5. Format summary comparison table nicely with R2 column.
"""
import json
from pathlib import Path

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])

        # 1. Update Cell 1 imports
        if 'from sklearn.metrics import mean_squared_error, mean_absolute_error' in src:
            src = src.replace(
                'from sklearn.metrics import mean_squared_error, mean_absolute_error',
                'from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score'
            )

        # 2. Update Cell 11 eval_metrics function
        if 'def eval_metrics(y_true, y_pred, model_name):' in src:
            old_eval = (
                "def eval_metrics(y_true, y_pred, model_name):\n"
                "    rmse = np.sqrt(mean_squared_error(y_true, y_pred))\n"
                "    mae  = mean_absolute_error(y_true, y_pred)\n"
                "    mape_val = mape(y_true, y_pred)\n"
                "    print(f'{model_name:<20}  RMSE={rmse:>12,.0f}  MAE={mae:>12,.0f}  MAPE={mape_val:>6.2f}%')\n"
                "    return {'model': model_name, 'RMSE': rmse, 'MAE': mae, 'MAPE': mape_val}"
            )
            new_eval = (
                "def eval_metrics(y_true, y_pred, model_name):\n"
                "    rmse = np.sqrt(mean_squared_error(y_true, y_pred))\n"
                "    mae  = mean_absolute_error(y_true, y_pred)\n"
                "    mape_val = mape(y_true, y_pred)\n"
                "    r2 = r2_score(y_true, y_pred)\n"
                "    print(f'{model_name:<24}  RMSE={rmse:>12,.0f}  MAE={mae:>12,.0f}  MAPE={mape_val:>6.2f}%  R²={r2:>6.3f}')\n"
                "    return {'model': model_name, 'RMSE': rmse, 'MAE': mae, 'MAPE': mape_val, 'R2': r2}"
            )
            src = src.replace(old_eval, new_eval)

        # 3. Update Cell 15 future forecast date offsets to month-end frequency
        if 'next_month = last_known[\'month\'].max() + pd.DateOffset(months=1)' in src:
            old_loop = (
                "future_preds = []\n"
                "for _ in range(6):\n"
                "    feat_row = build_lag_features(last_known, lags=[1, 2, 3, 6, 12])\n"
                "    if feat_row.empty:\n"
                "        break\n"
                "    X_fut = feat_row.iloc[[-1]][feat_cols].values\n"
                "    pred  = xgb_model.predict(X_fut)[0]\n"
                "    next_month = last_known['month'].max() + pd.DateOffset(months=1)\n"
                "    new_row = pd.DataFrame({'month': [next_month], 'revenue': [pred], 'orders': [np.nan]})\n"
                "    last_known = pd.concat([last_known, new_row], ignore_index=True)\n"
                "    future_preds.append({'month': next_month, 'predicted_revenue': round(pred, 2)})"
            )
            new_loop = (
                "future_dates = pd.date_range(start=monthly['month'].max(), periods=7, freq='ME')[1:]\n"
                "future_preds = []\n"
                "for next_month in future_dates:\n"
                "    feat_row = build_lag_features(last_known, lags=[1, 2, 3, 6, 12])\n"
                "    if feat_row.empty:\n"
                "        break\n"
                "    X_fut = feat_row.iloc[[-1]][feat_cols].values\n"
                "    pred  = float(xgb_model.predict(X_fut)[0])\n"
                "    new_row = pd.DataFrame({'month': [next_month], 'revenue': [pred], 'orders': [np.nan]})\n"
                "    last_known = pd.concat([last_known, new_row], ignore_index=True)\n"
                "    future_preds.append({'month': next_month.strftime('%Y-%m-%d'), 'predicted_revenue': round(pred, 2)})"
            )
            src = src.replace(old_loop, new_loop)

        # 4. Update Cell 17 sarima check
        if 'if \'sarima_fit\' in vars():' in src or 'if \'sarima_fit\' in dir():' in src:
            src = src.replace("if 'sarima_fit' in dir():", "if 'sarima_fit' in globals() or 'sarima_fit' in locals():")
            src = src.replace("if 'sarima_fit' in vars():", "if 'sarima_fit' in globals() or 'sarima_fit' in locals():")

        lines = src.split('\n')
        cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("NB03 patches applied.")
