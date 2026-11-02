import sys, joblib, numpy as np, pandas as pd
sys.path.insert(0, 'ml/scripts')
sys.path.insert(0, 'ml/scripts/custom_models')

obj = joblib.load('ml/models/sales_forecasting_selected.pkl')
m = obj['model']

# Test with 500-unit history
curr_history = [456.0, 376.0, 467.0, 527.0, 483.0, 415.0, 620.0, 742.0, 515.0, 584.0]
while len(curr_history) < 12:
    curr_history.insert(0, curr_history[0])

# Calculate scale relative to model domain
input_mean = float(np.mean(curr_history[-12:]))
model_mean = m.global_mean_velocity_ if hasattr(m, 'global_mean_velocity_') and m.global_mean_velocity_ > 0 else 18.0
scale_factor = input_mean / model_mean if model_mean > 0 else 1.0

print(f"Input mean: {input_mean:.2f}, Model mean: {model_mean:.2f}, Scale factor: {scale_factor:.2f}")

# Scale-normalized recursive forecast
norm_history = [h / scale_factor for h in curr_history]
start_year, start_month = 2026, 10
preds = []

for i in range(6):
    m_idx = (start_month + i - 1) % 12 + 1
    y_idx = start_year + (start_month + i - 1) // 12
    quarter = (m_idx - 1) // 3 + 1
    feat_dict = {
        'quantity': norm_history[-1],
        'lag_1': norm_history[-1],
        'lag_2': norm_history[-2],
        'lag_3': norm_history[-3],
        'lag_12': norm_history[-12],
        'roll3_mean': float(np.mean(norm_history[-3:])),
        'roll6_mean': float(np.mean(norm_history[-6:])),
        'roll3_std': float(np.std(norm_history[-3:])),
        'month_num': float(m_idx),
        'quarter': float(quarter),
        'year': float(y_idx),
        'is_q4': 1.0 if quarter == 4 else 0.0,
        'is_q1': 1.0 if quarter == 1 else 0.0,
    }
    feat_df = pd.DataFrame([feat_dict])
    pred_norm = float(m.predict(feat_df)[0])
    pred_norm = max(0.5, pred_norm)
    pred_units = pred_norm * scale_factor
    preds.append((f"{y_idx}-{m_idx:02d}", round(pred_units, 2)))
    norm_history.append(pred_norm)

print("Scale-normalized forecast for 6 months:")
for p in preds:
    print(f"  {p[0]}: {p[1]} units")
