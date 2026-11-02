import sys, joblib, numpy as np, pandas as pd
from datetime import datetime

sys.path.insert(0, 'backend')
sys.path.insert(0, 'ml/scripts')
sys.path.insert(0, 'ml/scripts/custom_models')
from app.ml.model_loader import ModelLoader

loader = ModelLoader()
loader.load_all_models()

def simulate_predict_sales(model_key, history, months_ahead=6, entity_id=None):
    model_obj = loader.get_model(model_key)
    model = model_obj["model"]
    feat_cols = model_obj.get("feature_cols", [])
    
    curr_history = list(history)
    while len(curr_history) < 12:
        curr_history.insert(0, curr_history[0] if curr_history else 100.0)
        
    input_scale = float(np.mean(curr_history[-12:]))
    model_domain_mean = getattr(model, "global_mean_velocity_", 18.0) or 18.0
    scale = input_scale / model_domain_mean if model_domain_mean > 0 and input_scale > 0 else 1.0
    
    norm_history = [h / scale for h in curr_history]
    start_year, start_month = 2026, 10
    predictions = []
    
    for i in range(months_ahead):
        m_idx = (start_month + i - 1) % 12 + 1
        y_idx = start_year + (start_month + i - 1) // 12
        quarter = (m_idx - 1) // 3 + 1
        target_date = f"{y_idx:04d}-{m_idx:02d}-28"
        
        feat_dict = {
            "quantity": norm_history[-1],
            "lag_1": norm_history[-1],
            "lag_2": norm_history[-2],
            "lag_3": norm_history[-3],
            "lag_12": norm_history[-12],
            "roll3_mean": float(np.mean(norm_history[-3:])),
            "roll6_mean": float(np.mean(norm_history[-6:])),
            "roll3_std": float(np.std(norm_history[-3:])),
            "month_num": float(m_idx),
            "quarter": float(quarter),
            "year": float(y_idx),
            "is_q4": 1.0 if quarter == 4 else 0.0,
            "is_q1": 1.0 if quarter == 1 else 0.0,
            "is_jan": 1.0 if m_idx == 1 else 0.0,
        }
        if entity_id:
            feat_dict["product_id"] = entity_id
            
        if hasattr(model, "product_velocity_") or hasattr(model, "weights") or hasattr(model, "trend_anchor"):
            feat_df = pd.DataFrame([feat_dict])
            pred_norm = float(model.predict(feat_df)[0])
        else:
            X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
            pred_norm = float(model.predict(X)[0])
            
        # Robust floor to prevent collapse
        norm_floor = max(0.2, float(np.min(norm_history[-6:])) * 0.25)
        pred_norm = max(norm_floor, pred_norm)
        pred_units = pred_norm * scale
        
        predictions.append((target_date, round(pred_units, 2)))
        norm_history.append(pred_norm)
        
    return predictions

supermarket_agg = [456.0, 376.0, 467.0, 527.0, 483.0, 415.0, 620.0, 742.0, 515.0, 584.0]
bread_sku = [15.0, 12.0, 38.0, 29.0, 45.0, 25.0, 50.0, 60.0, 7.0, 27.0]

print("=== TEST 1: Supermarket Aggregate (All Products) with PPF for 1, 2, 3, 6, 12 months ===")
for m in [1, 2, 3, 6, 12]:
    preds = simulate_predict_sales("sales_selected", supermarket_agg, months_ahead=m)
    print(f"Horizon {m}m: {preds}")

print("\n=== TEST 2: Product Bread SKU for 1, 2, 3, 6, 12 months ===")
for m in [1, 2, 3, 6, 12]:
    preds = simulate_predict_sales("sales_selected", bread_sku, months_ahead=m)
    print(f"Horizon {m}m: {preds}")

print("\n=== TEST 3: All Candidate Models for 6 months ahead ===")
for mk in ["sales_selected", "sales_aagf_product", "sales_lgb_product", "sales_xgb_product", "sales_linear_regression_product"]:
    preds = simulate_predict_sales(mk, supermarket_agg, months_ahead=6)
    print(f"Model {mk:32s}: {preds}")
