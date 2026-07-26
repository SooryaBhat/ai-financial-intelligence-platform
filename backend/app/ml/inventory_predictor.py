"""
Inventory Demand & Stock Optimization Predictor.
Uses trained XGBoost inventory model to predict monthly demand and optimize reorder points.
"""
from datetime import datetime
import numpy as np
from typing import Dict, List

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    InventoryPredictionRequest,
    InventoryPredictionResponse,
)


def _default_inventory_demand_history() -> List[float]:
    """Default historical monthly demand units."""
    return [320.0, 310.0, 350.0, 380.0, 410.0, 395.0, 420.0]


def predict_inventory(
    request: InventoryPredictionRequest,
    loader: ModelLoader,
) -> InventoryPredictionResponse:
    """
    Predict monthly demand and compute inventory optimization metrics.
    """
    try:
        model_obj = loader.get_model("inventory_demand")
        if not model_obj or not isinstance(model_obj, dict):
            raise ValueError("Inventory demand model artifact is not available.")

        model = model_obj["model"]
        feat_cols = model_obj["feature_cols"]

        history = request.historical_monthly_demand or _default_inventory_demand_history()
        while len(history) < 6:
            history.insert(0, history[0] if history else 300.0)

        current_date = datetime.now()
        m_idx = current_date.month
        y_idx = current_date.year
        quarter = (m_idx - 1) // 3 + 1

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
                "month_num": float(m_idx),
                "quarter": float(quarter),
                "year": float(y_idx),
                "is_q4": 1.0 if quarter == 4 else 0.0,
                "is_q1": 1.0 if quarter == 1 else 0.0,
            }

        X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
        predicted_demand = float(model.predict(X)[0])
        predicted_demand = max(10.0, predicted_demand)

        # Inventory Optimization Calculations
        daily_demand = predicted_demand / 30.0
        lead_time_days = request.lead_time_days
        safety_stock = daily_demand * 7.0  # 7-day safety buffer
        reorder_point = (daily_demand * lead_time_days) + safety_stock
        reorder_quantity = max(50.0, predicted_demand * 1.2)

        days_supply = request.current_stock / (daily_demand + 1e-6)

        if days_supply <= 7.0:
            risk_level = "CRITICAL"
        elif days_supply <= 14.0:
            risk_level = "HIGH"
        elif days_supply <= 30.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        reorder_rec = request.current_stock <= reorder_point

        return InventoryPredictionResponse(
            product_id=request.product_id,
            product_name=request.product_name or "Target Product",
            current_stock=request.current_stock,
            predicted_monthly_demand=round(predicted_demand, 2),
            recommended_reorder_point=round(reorder_point, 2),
            recommended_reorder_quantity=round(reorder_quantity, 2),
            stockout_risk_level=risk_level,
            days_of_supply_remaining=round(days_supply, 1),
            reorder_recommended=reorder_rec,
        )
    except Exception as e:
        logger.error("[InventoryPredictor] Prediction failed: {}", e)
        raise e
