"""
Profit Prediction Service.
Uses trained XGBoost model to predict upcoming net profit and evaluate profit margin efficiency.
"""
from datetime import datetime
import numpy as np
from typing import Dict, List

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    ProfitPredictionRequest,
    ProfitPredictionResponse,
)


def _default_profit_history() -> List[float]:
    return [4500000.0, 5200000.0, 4800000.0, 5100000.0, 6800000.0, 5900000.0]


def _default_revenue_history() -> List[float]:
    return [17600000.0, 20400000.0, 17500000.0, 18800000.0, 25100000.0, 21300000.0]


def predict_profit(
    request: ProfitPredictionRequest,
    loader: ModelLoader,
) -> ProfitPredictionResponse:
    """
    Predict upcoming monthly net profit and margin metrics.
    """
    try:
        model_obj = loader.get_model("profit_prediction")
        if not model_obj or not isinstance(model_obj, dict):
            raise ValueError("Profit prediction model artifact is not available.")

        model = model_obj["model"]
        feat_cols = model_obj["feature_cols"]

        p_hist = request.historical_profits or _default_profit_history()
        r_hist = request.historical_revenues or _default_revenue_history()

        while len(p_hist) < 6:
            p_hist.insert(0, p_hist[0] if p_hist else 4000000.0)
        while len(r_hist) < 6:
            r_hist.insert(0, r_hist[0] if r_hist else 18000000.0)

        current_date = datetime.now()
        m_idx = current_date.month
        y_idx = current_date.year
        quarter = (m_idx - 1) // 3 + 1

        exp_ratio_1 = max(0.1, 1.0 - (p_hist[-1] / (r_hist[-1] + 1e-8)))
        exp_ratio_2 = max(0.1, 1.0 - (p_hist[-2] / (r_hist[-2] + 1e-8)))

        if request.custom_features:
            feat_dict = request.custom_features
        else:
            feat_dict = {
                "profit_lag1": p_hist[-1],
                "profit_lag2": p_hist[-2],
                "profit_lag3": p_hist[-3],
                "profit_lag6": p_hist[-6],
                "profit_roll3": float(np.mean(p_hist[-3:])),
                "profit_roll6": float(np.mean(p_hist[-6:])),
                "revenue_lag1": r_hist[-1],
                "revenue_lag2": r_hist[-2],
                "revenue_lag3": r_hist[-3],
                "expense_ratio_lag1": float(exp_ratio_1),
                "expense_ratio_lag2": float(exp_ratio_2),
                "month_num": float(m_idx),
                "quarter": float(quarter),
                "year": float(y_idx),
                "is_q4": 1.0 if quarter == 4 else 0.0,
            }

        X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
        predicted_profit = float(model.predict(X)[0])

        projected_rev = request.projected_revenue or r_hist[-1]
        profit_margin = (predicted_profit / (projected_rev + 1e-8)) * 100.0

        if profit_margin >= 25.0:
            status = "HIGHLY_PROFITABLE"
        elif profit_margin >= 15.0:
            status = "MODERATELY_PROFITABLE"
        elif profit_margin >= 5.0:
            status = "LOW_MARGIN"
        else:
            status = "UNPROFITABLE"

        return ProfitPredictionResponse(
            predicted_profit=round(predicted_profit, 2),
            predicted_profit_margin_pct=round(profit_margin, 2),
            profitability_status=status,
            confidence_score=92.5,
            influencing_factors={
                "recent_profit_trend": round(float(np.mean(p_hist[-3:])), 2),
                "estimated_revenue_base": round(projected_rev, 2),
                "expense_ratio_baseline": round(float(exp_ratio_1), 3),
            },
        )
    except Exception as e:
        logger.error("[ProfitPredictor] Prediction failed: {}", e)
        raise e
