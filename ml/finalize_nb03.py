"""
finalize_nb03.py
================
Finalize exact formatting for 03_revenue_forecasting.ipynb.
"""
import json
from pathlib import Path

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])

        # Update Cell 11
        if 'def eval_metrics(y_true, y_pred, model_name):' in src:
            src = (
                "def mape(y_true, y_pred):\n"
                "    return np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), 1e-8))) * 100\n\n"
                "def eval_metrics(y_true, y_pred, model_name):\n"
                "    rmse = np.sqrt(mean_squared_error(y_true, y_pred))\n"
                "    mae  = mean_absolute_error(y_true, y_pred)\n"
                "    mape_val = mape(y_true, y_pred)\n"
                "    r2   = r2_score(y_true, y_pred)\n"
                "    print(f'{model_name:<24}  RMSE={rmse:>12,.0f}  MAE={mae:>12,.0f}  MAPE={mape_val:>6.2f}%  R²={r2:>6.3f}')\n"
                "    return {'model': model_name, 'RMSE': round(rmse, 2), 'MAE': round(mae, 2), 'MAPE_%': round(mape_val, 2), 'R2': round(r2, 4)}\n\n"
                "results = []\n"
                "forecasts = {}\n\n"
                "# ── Model A: Naïve Baseline (last observed value) ─────────────────────────────\n"
                "naive_pred = np.full(len(test_ts), train_ts.iloc[-1])\n"
                "results.append(eval_metrics(test_ts.values, naive_pred, 'Naive Baseline'))\n"
                "forecasts['Naive'] = pd.Series(naive_pred, index=test_ts.index)\n\n"
                "# ── Model B: SARIMA ───────────────────────────────────────────────────────────\n"
                "try:\n"
                "    sarima = SARIMAX(\n"
                "        train_ts,\n"
                "        order=(1, d_order, 1),\n"
                "        seasonal_order=(1, 1, 0, 12),\n"
                "        enforce_stationarity=False,\n"
                "        enforce_invertibility=False,\n"
                "    )\n"
                "    sarima_fit = sarima.fit(disp=False)\n"
                "    sarima_pred = sarima_fit.forecast(steps=len(test_ts))\n"
                "    sarima_pred.index = test_ts.index\n"
                "    results.append(eval_metrics(test_ts.values, sarima_pred.values, 'SARIMA(1,d,1)(1,1,0,12)'))\n"
                "    forecasts['SARIMA'] = sarima_pred\n"
                "except Exception as e:\n"
                "    print(f'SARIMA failed: {e}')\n\n"
                "# ── Model C: XGBoost with lag features ───────────────────────────────────────\n"
                "def build_lag_features(df: pd.DataFrame, lags: list, target: str = 'revenue') -> pd.DataFrame:\n"
                "    \"\"\"Build lag and rolling mean features from a monthly revenue DataFrame.\"\"\"\n"
                "    d = df.copy()\n"
                "    for lag in lags:\n"
                "        d[f'lag_{lag}'] = d[target].shift(lag)\n"
                "    d['roll3_mean'] = d[target].shift(1).rolling(3, min_periods=1).mean()\n"
                "    d['roll6_mean'] = d[target].shift(1).rolling(6, min_periods=1).mean()\n"
                "    d['month_num']  = d['month'].dt.month\n"
                "    d['quarter']    = d['month'].dt.quarter\n"
                "    return d.dropna()\n\n"
                "feat_df = build_lag_features(monthly, lags=[1, 2, 3, 6, 12])\n"
                "feat_cols = [c for c in feat_df.columns if c.startswith('lag_') or\n"
                "             c in ['roll3_mean', 'roll6_mean', 'month_num', 'quarter']]\n\n"
                "# Re-split on the lag-enriched frame\n"
                "train_xgb = feat_df[feat_df['month'] <= train_df['month'].max()]\n"
                "test_xgb  = feat_df[feat_df['month'] >  train_df['month'].max()]\n\n"
                "X_tr, y_tr = train_xgb[feat_cols].values, train_xgb['revenue'].values\n"
                "X_te, y_te = test_xgb[feat_cols].values,  test_xgb['revenue'].values\n\n"
                "xgb_model = xgb.XGBRegressor(\n"
                "    n_estimators=300,\n"
                "    learning_rate=0.05,\n"
                "    max_depth=4,\n"
                "    subsample=0.8,\n"
                "    colsample_bytree=0.8,\n"
                "    random_state=42,\n"
                "    verbosity=0,\n"
                ")\n"
                "xgb_model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)\n"
                "xgb_pred = xgb_model.predict(X_te)\n\n"
                "results.append(eval_metrics(y_te, xgb_pred, 'XGBoost'))\n"
                "forecasts['XGBoost'] = pd.Series(xgb_pred, index=test_xgb['month'])\n\n"
                "# ── Model D: LightGBM ─────────────────────────────────────────────────────────\n"
                "try:\n"
                "    import lightgbm as lgb\n"
                "    lgb_model = lgb.LGBMRegressor(\n"
                "        n_estimators=300,\n"
                "        learning_rate=0.05,\n"
                "        max_depth=4,\n"
                "        subsample=0.8,\n"
                "        colsample_bytree=0.8,\n"
                "        random_state=42,\n"
                "        verbosity=-1,\n"
                "    )\n"
                "    lgb_model.fit(X_tr, y_tr)\n"
                "    lgb_pred = lgb_model.predict(X_te)\n"
                "    results.append(eval_metrics(y_te, lgb_pred, 'LightGBM'))\n"
                "    forecasts['LightGBM'] = pd.Series(lgb_pred, index=test_xgb['month'])\n"
                "except ImportError:\n"
                "    print('LightGBM not installed — skipping.')\n\n"
                "print('\\nModel training complete.')"
            )

        # Update Cell 13
        if "results_df = pd.DataFrame(results)" in src:
            src = (
                "# Summarise all model results in a comparison table\n"
                "results_df = pd.DataFrame(results).sort_values('MAPE_%')\n"
                "print('=== Revenue Forecasting — Model Comparison ===')\n"
                "print(results_df.to_string(index=False))\n\n"
                "best_model_name = results_df.iloc[0]['model']\n"
                "print(f'\\n[Best Model] Best model by MAPE: {best_model_name}')\n\n"
                "# Save evaluation report\n"
                "report = {\n"
                "    'task': 'revenue_forecasting',\n"
                "    'models': results,\n"
                "    'best_model': best_model_name,\n"
                "}\n"
                "with open(os.path.join(REPORTS_DIR, 'revenue_forecasting_eval.json'), 'w') as f:\n"
                "    json.dump(report, f, indent=2)\n"
                "print('Evaluation report saved.')"
            )

        lines = src.split('\n')
        cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Finalize script executed.")
