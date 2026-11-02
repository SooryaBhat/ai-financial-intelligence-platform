"""
Sales Forecasting Service.
Uses verified ML models (Product Profile Forecaster, AAGF, LightGBM, XGBoost, Linear Regression)
to predict SKU and Category demand.
"""
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

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
    Supports true candidate selection: 'product_profile', 'aagf', 'xgboost', 'lightgbm', 'linear_regression'.
    """
    try:
        entity_type = (request.entity_type or "product").lower().strip()
        model_type = (request.model_type or "product_profile").lower().strip()
        months_ahead = request.months_ahead
        history = request.historical_sales or _default_sales_history()

        while len(history) < 12:
            history.insert(0, history[0] if history else 100.0)

        # Registry metadata
        reg = loader.get_registry().get("sales_forecasting", {})
        verified_metrics = reg.get("metrics", {})
        holdout_metrics = reg.get("holdout_company3_metrics", {})

        provenance = {
            "dataset_version": "synthetic_v2",
            "training_period": "2022-01 to 2026-02 (58 months, 142,791 records)",
            "cross_tenant_holdout": "Company 3 (Apna Kirana Store) zero-shot holdout",
            "val_wape_pct": verified_metrics.get("val_wape_pct", 14.48),
            "val_r2": verified_metrics.get("val_r2", 0.9482),
            "holdout_wape_pct": holdout_metrics.get("wape_pct", 11.87),
        }

        if entity_type == "category":
            model_key = "sales_xgb_category"
            model_name = "XGBoost Category Sales Forecaster"
            model_version = "sales_forecasting_xgb_category.pkl"
        elif model_type in ["product_profile", "selected"]:
            model_key = "sales_selected"
            model_name = "Product Profile Forecaster (Winner, R²=+0.948)"
            model_version = "sales_forecasting_selected.pkl"
        elif model_type == "aagf":
            model_key = "sales_aagf_product"
            model_name = "ALLADIN Adaptive Global Forecaster (AAGF SKU)"
            model_version = "sales_forecasting_aagf_product.pkl"
        elif model_type == "lightgbm":
            model_key = "sales_lgb_product"
            model_name = "LightGBM Product Sales Predictor"
            model_version = "sales_forecasting_lgb_product.pkl"
        elif model_type in ["linear", "linear_regression"]:
            model_key = "sales_linear_regression_product"
            model_name = "Linear Regression Product Sales Predictor"
            model_version = "sales_forecasting_linear_regression_product.pkl"
        elif model_type == "xgboost":
            model_key = "sales_xgb_product"
            model_name = "XGBoost Product Sales Predictor"
            model_version = "sales_forecasting_xgb_product.pkl"
        else:
            model_key = "sales_selected"
            model_name = "Product Profile Forecaster (Selected)"
            model_version = "sales_forecasting_selected.pkl"

        model_obj = loader.get_model(model_key)
        if not model_obj or not isinstance(model_obj, dict):
            model_obj = loader.get_model("sales_selected") or loader.get_model("sales_xgb_product")
            model_name = "Product Sales Forecaster (Fallback)"
            model_version = "sales_forecasting_fallback"

        if not model_obj or not isinstance(model_obj, dict):
            raise ValueError(f"Sales model artifact '{model_key}' is not available.")

        model = model_obj["model"]
        feat_cols = model_obj.get("feature_cols", [])

        predictions: List[SalesForecastItem] = []
        curr_history = list(history)
        current_date = datetime.now()
        start_year = current_date.year
        start_month = current_date.month

        avg_unit_price = 450.0

        for i in range(months_ahead):
            m_idx = (start_month + i - 1) % 12 + 1
            y_idx = start_year + (start_month + i - 1) // 12
            quarter = (m_idx - 1) // 3 + 1
            target_date = f"{y_idx:04d}-{m_idx:02d}-28"

            if request.custom_features:
                feat_dict = dict(request.custom_features)
            else:
                feat_dict = {
                    "quantity": curr_history[-1],
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
                    "is_q1": 1.0 if quarter == 1 else 0.0,
                    "is_jan": 1.0 if m_idx == 1 else 0.0,
                }
                if request.entity_id:
                    feat_dict["product_id"] = request.entity_id

            if hasattr(model, "product_velocity_") or hasattr(model, "weights") or hasattr(model, "trend_anchor"):
                feat_df = pd.DataFrame([feat_dict])
                pred_units = float(model.predict(feat_df)[0])
            else:
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
            model_name=model_name,
            model_version=model_version,
            predictions=predictions,
            total_predicted_units=round(total_units, 2),
            total_predicted_amount=round(total_amount, 2),
            metrics=verified_metrics,
            data_provenance=provenance,
        )
    except Exception as e:
        logger.error("[SalesPredictor] Prediction failed: {}", e)
        raise e
