"""
Sales Forecasting Service.
Uses XGBoost or LightGBM models to predict product/category sales demand.
"""
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, List

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    SalesForecastItem,
    SalesPredictionRequest,
    SalesPredictionResponse,
)


def _default_sales_history() -> List[float]:
    """Default monthly sales units history."""
    return [120.0, 135.0, 128.0, 142.0, 160.0, 155.0, 168.0, 175.0, 162.0, 180.0, 210.0, 245.0]


def predict_sales(
    request: SalesPredictionRequest,
    loader: ModelLoader,
) -> SalesPredictionResponse:
    """
    Generate sales forecasts per product or category.
    """
    try:
        entity_type = request.entity_type.lower()
        model_type = request.model_type.lower()
        months_ahead = request.months_ahead
        history = request.historical_sales or _default_sales_history()

        while len(history) < 12:
            history.insert(0, history[0] if history else 100.0)

        if entity_type == "category":
            model_key = "sales_xgb_category"
            model_name = "XGBoost Category Sales Predictor"
        elif model_type == "lightgbm":
            model_key = "sales_lgb_product"
            model_name = "LightGBM Product Sales Predictor"
        else:
            model_key = "sales_xgb_product"
            model_name = "XGBoost Product Sales Predictor"

        model_obj = loader.get_model(model_key)
        if not model_obj or not isinstance(model_obj, dict):
            # Fallback to product xgb
            model_obj = loader.get_model("sales_xgb_product")
            model_name = "XGBoost Product Sales Predictor (Fallback)"

        if not model_obj:
            raise ValueError(f"Sales model artifact '{model_key}' is not available.")

        model = model_obj["model"]
        feat_cols = model_obj["feature_cols"]

        predictions: List[SalesForecastItem] = []
        curr_history = list(history)
        current_date = datetime.now()
        start_year = current_date.year
        start_month = current_date.month

        avg_unit_price = 450.0  # Estimated average price per unit

        for i in range(months_ahead):
            m_idx = (start_month + i - 1) % 12 + 1
            y_idx = start_year + (start_month + i - 1) // 12
            quarter = (m_idx - 1) // 3 + 1
            target_date = f"{y_idx:04d}-{m_idx:02d}-28"

            if request.custom_features:
                feat_dict = request.custom_features
            else:
                feat_dict = {
                    "lag_1": curr_history[-1],
                    "lag_2": curr_history[-2],
                    "lag_3": curr_history[-3],
                    "lag_12": curr_history[-12],
                    "roll3_mean": float(np.mean(curr_history[-3:])),
                    "roll6_mean": float(np.mean(curr_history[-6:])),
                    "roll3_std": float(np.std(curr_history[-3:])),
                    "month_num": float(m_idx),
                    "quarter": float(quarter),
                    "year": float(y_idx),
                    "is_q4": 1.0 if quarter == 4 else 0.0,
                    "is_jan": 1.0 if m_idx == 1 else 0.0,
                }

            X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
            pred_units = float(model.predict(X)[0])
            pred_units = max(1.0, pred_units)
            pred_amount = pred_units * avg_unit_price

            predictions.append(
                SalesForecastItem(
                    month=target_date,
                    predicted_units_sold=round(pred_units, 2),
                    predicted_sales_amount=round(pred_amount, 2),
                )
            )
            curr_history.append(pred_units)

        total_units = sum(p.predicted_units_sold for p in predictions)
        total_amount = sum(p.predicted_sales_amount for p in predictions)

        return SalesPredictionResponse(
            entity_type=entity_type,
            entity_id=request.entity_id,
            model_used=model_name,
            predictions=predictions,
            total_predicted_units=round(total_units, 2),
            total_predicted_amount=round(total_amount, 2),
        )
    except Exception as e:
        logger.error("[SalesPredictor] Prediction failed: {}", e)
        raise e
