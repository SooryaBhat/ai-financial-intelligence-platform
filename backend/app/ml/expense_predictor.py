"""
Expense Prediction Service.
Uses XGBoost or Linear Regression models to forecast operational expenses and detect risk surges.
"""
from datetime import datetime
import numpy as np
from typing import Dict, List

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    ExpensePredictionRequest,
    ExpensePredictionResponse,
)


def _default_expense_history() -> List[float]:
    return [2200000.0, 2450000.0, 2300000.0, 2600000.0, 2800000.0, 2750000.0]


def predict_expense(
    request: ExpensePredictionRequest,
    loader: ModelLoader,
) -> ExpensePredictionResponse:
    """
    Predict monthly expense baseline and evaluate risk alerts.
    """
    try:
        model_type = request.model_type.lower()
        if model_type == "linear_regression":
            model_obj = loader.get_model("expense_linear_regression")
            model_name = "Linear Regression Expense Predictor"
        else:
            model_obj = loader.get_model("expense_xgboost")
            model_name = "XGBoost Expense Predictor"

        if not model_obj or not isinstance(model_obj, dict):
            model_obj = loader.get_model("expense_xgboost")
            model_name = "XGBoost Expense Predictor (Fallback)"

        if not model_obj:
            raise ValueError("Expense prediction model is not available.")

        model = model_obj["model"]
        feat_cols = model_obj["feature_cols"]

        history = request.historical_expenses or _default_expense_history()
        while len(history) < 6:
            history.insert(0, history[0] if history else 2000000.0)

        current_date = datetime.now()
        m_idx = current_date.month
        y_idx = current_date.year
        quarter = (m_idx - 1) // 3 + 1

        selected_cat = request.category or "All Categories"

        if request.custom_features:
            feat_dict = request.custom_features
        else:
            feat_dict = {
                "lag_1": history[-1],
                "lag_2": history[-2],
                "lag_3": history[-3],
                "lag_6": history[-6],
                "roll3_mean": float(np.mean(history[-3:])),
                "roll6_mean": float(np.mean(history[-6:])),
                "roll3_std": float(np.std(history[-3:])),
                "txn_count": 85.0,
                "avg_expense": float(np.mean(history[-3:]) / 85.0),
                "month_num": float(m_idx),
                "quarter": float(quarter),
                "year": float(y_idx),
                "is_q4": 1.0 if quarter == 4 else 0.0,
                "is_q1": 1.0 if quarter == 1 else 0.0,
            }

            # Set category dummy variables
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

        category_breakdown = {
            "Salaries & Payroll": round(predicted_expense * 0.45, 2),
            "Rent & Utilities": round(predicted_expense * 0.20, 2),
            "Marketing & Growth": round(predicted_expense * 0.15, 2),
            "IT & Software": round(predicted_expense * 0.10, 2),
            "Logistics & Operational": round(predicted_expense * 0.10, 2),
        }

        return ExpensePredictionResponse(
            model_used=model_name,
            category=selected_cat,
            predicted_expense=round(predicted_expense, 2),
            predicted_transaction_count=int(feat_dict.get("txn_count", 85)),
            expense_risk_alert=risk_alert,
            category_breakdown=category_breakdown,
        )
    except Exception as e:
        logger.error("[ExpensePredictor] Prediction failed: {}", e)
        raise e
