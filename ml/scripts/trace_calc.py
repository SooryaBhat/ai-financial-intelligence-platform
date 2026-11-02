import sys, joblib, numpy as np, pandas as pd
sys.path.insert(0, 'ml/scripts')
sys.path.insert(0, 'ml/scripts/custom_models')

obj = joblib.load('ml/models/sales_forecasting_selected.pkl')
m = obj['model']
curr_history = [456.0, 376.0, 467.0, 527.0, 483.0, 415.0, 620.0, 742.0, 515.0, 584.0]
while len(curr_history) < 12:
    curr_history.insert(0, curr_history[0])

start_year, start_month = 2026, 10
for i in range(6):
    m_idx = (start_month + i - 1) % 12 + 1
    y_idx = start_year + (start_month + i - 1) // 12
    quarter = (m_idx - 1) // 3 + 1
    feat_dict = {
        'quantity': curr_history[-1],
        'lag_1': curr_history[-1],
        'lag_2': curr_history[-2],
        'lag_3': curr_history[-3],
        'lag_12': curr_history[-12],
        'roll3_mean': float(np.mean(curr_history[-3:])),
        'roll6_mean': float(np.mean(curr_history[-6:])),
        'roll3_std': float(np.std(curr_history[-3:])),
        'month_num': float(m_idx),
        'quarter': float(quarter),
        'year': float(y_idx),
        'is_q4': 1.0 if quarter == 4 else 0.0,
        'is_q1': 1.0 if quarter == 1 else 0.0,
    }
    feat_df = pd.DataFrame([feat_dict])
    X_num = feat_df[m.feature_cols_].select_dtypes(include=[np.number]).fillna(0.0).values
    resid = float(m.ridge_model_.predict(X_num)[0])
    raw_pred = m.global_mean_velocity_ + resid
    clamped_pred = max(1.0, raw_pred)
    
    roll6_idx = m.feature_cols_.index('roll6_mean')
    roll6_coef = m.ridge_model_.coef_[roll6_idx]
    qty_idx = m.feature_cols_.index('quantity')
    qty_coef = m.ridge_model_.coef_[qty_idx]
    
    print(f"Step {i+1} (Y={y_idx}, M={m_idx:02d}): raw_pred={raw_pred:.2f}, clamped={clamped_pred:.2f}")
    print(f"   resid={resid:.2f}, base_vel={m.global_mean_velocity_:.2f}, intercept={m.ridge_model_.intercept_:.2f}")
    print(f"   quantity={feat_dict['quantity']:.1f} * {qty_coef:.3f} = {feat_dict['quantity']*qty_coef:.2f}")
    print(f"   roll6_mean={feat_dict['roll6_mean']:.1f} * {roll6_coef:.3f} = {feat_dict['roll6_mean']*roll6_coef:.2f}")
    for col in m.feature_cols_:
        c_idx = m.feature_cols_.index(col)
        c_val = feat_dict[col]
        c_coef = m.ridge_model_.coef_[c_idx]
        print(f"      {col:10s}: val={c_val:8.2f}, coef={c_coef:8.4f}, contrib={c_val*c_coef:8.2f}")
    curr_history.append(clamped_pred)
