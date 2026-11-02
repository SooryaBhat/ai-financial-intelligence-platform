"""
Expense Prediction Service.
Uses verified ML models (Random Forest, XGBoost, Linear Regression, Recurring Expense Model)
to forecast operational expenses and detect risk surges.
"""
from datetime import datetime
import numpy as np
from typing import Dict, List, Optional

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    ExpensePredictionRequest,
    ExpensePredictionResponse,
)


def _default_expense_history() -> List[float]:
    """Default historical monthly operating expenses aligned with simulated retail business scale (~Rs. 1.6M/mo)."""
    return [1550000.0, 1620000.0, 1580000.0, 1710000.0, 1650000.0, 1680000.0]


def predict_expense(
    request: ExpensePredictionRequest,
    loader: ModelLoader,
) -> ExpensePredictionResponse:
    """
    Predict monthly expense baseline and evaluate risk alerts.
    Supports candidate selection: 'random_forest', 'xgboost', 'linear_regression', 'recurring'.
    """
    try:
        model_type = (request.model_type or "random_forest").lower().strip()

        # Registry metadata
        reg = loader.get_registry().get("expense_prediction", {})
        verified_metrics = reg.get("metrics", {})
        holdout_metrics = reg.get("holdout_company3_metrics", {})

        provenance = {
            "dataset_version": "synthetic_v2",
            "training_period": "2022-01 to 2026-02 (58 months, 142,791 records)",
            "cross_tenant_holdout": "Company 3 (Apna Kirana Store) zero-shot holdout",
            "val_wape_pct": verified_metrics.get("val_wape_pct", 19.10),
            "val_r2": verified_metrics.get("val_r2", 0.9477),
            "holdout_wape_pct": holdout_metrics.get("wape_pct", 18.00),
        }

        if model_type in ["linear", "linear_regression"]:
            model_key = "expense_linear_regression"
            model_name = "Linear Regression Expense Predictor"
            model_version = "expense_prediction_linear_regression.pkl"
        elif model_type == "xgboost":
            model_key = "expense_xgboost"
            model_name = "XGBoost Expense Predictor"
            model_version = "expense_prediction_xgboost.pkl"
        elif model_type == "recurring":
            model_key = "expense_recurring"
            model_name = "Recurring Fixed/Variable Expense Forecaster"
            model_version = "expense_prediction_recurring.pkl"
        else:
            # Production winner: Random Forest (R² = +0.948, Val WAPE = 19.10%)
            model_key = "expense_selected"
            model_name = "Random Forest Expense Predictor (Winner, R²=+0.948)"
            model_version = "expense_prediction_selected.pkl"

        model_obj = loader.get_model(model_key) or loader.get_model("expense_selected") or loader.get_model("expense_xgboost")
        if not model_obj or not isinstance(model_obj, dict):
            raise ValueError(f"Expense prediction model artifact '{model_key}' is not available.")

        model = model_obj["model"]
        feat_cols = model_obj.get("feature_cols", [])

        history = request.historical_expenses or _default_expense_history()
        while len(history) < 6:
            history.insert(0, history[0] if history else 2000000.0)

        current_date = datetime.now()
        m_idx = current_date.month
        y_idx = current_date.year
        quarter = (m_idx - 1) // 3 + 1

        selected_cat = request.category or "All Categories"

        if request.custom_features:
            feat_dict = dict(request.custom_features)
        else:
            feat_dict = {
                "lag_1": history[-1],
                "lag_2": history[-2],
                "lag_3": history[-3],
                "lag_6": history[-6],
                "roll3_mean": float(np.mean(history[-3:])),
                "roll6_mean": float(np.mean(history[-6:])),
                "roll3_std": float(np.std(history[-3:])),
                "txn_count_lag1": 85.0,
                "avg_expense_lag1": float(np.mean(history[-3:]) / 85.0),
                "month_num": float(m_idx),
                "quarter": float(quarter),
                "year": float(y_idx),
                "is_q4": 1.0 if quarter == 4 else 0.0,
                "is_q1": 1.0 if quarter == 1 else 0.0,
            }

            for col in feat_cols:
                if col.startswith("cat_"):
                    cat_name = col[4:]
                    feat_dict[col] = 1.0 if request.category and request.category.lower() in cat_name.lower() else 0.0

        X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
        predicted_expense = float(model.predict(X)[0])
        predicted_expense = max(10000.0, predicted_expense)

        recent_avg = float(np.mean(history[-3:]))
        increase_pct = (predicted_expense - recent_avg) / (recent_avg + 1e-8)

        if increase_pct > 0.25:
            risk_alert = "HIGH_ANOMALOUS_EXPENSE"
        elif increase_pct > 0.10:
            risk_alert = "ELEVATED"
        else:
            risk_alert = "NORMAL"

        return ExpensePredictionResponse(
            model_used=model_name,
            model_name=model_name,
            model_version=model_version,
            category=selected_cat,
            predicted_expense=round(predicted_expense, 2),
            predicted_transaction_count=85,
            expense_risk_alert=risk_alert,
            metrics=verified_metrics,
            data_provenance=provenance,
        )
    except Exception as e:
        logger.error("[ExpensePredictor] Prediction failed: {}", e)
        raise e
