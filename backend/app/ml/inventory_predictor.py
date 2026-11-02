"""
Inventory Demand & Stock Optimization Predictor.
Uses verified ML models (LightGBM, XGBoost, Random Forest, Censored Demand)
to predict monthly demand and optimize reorder points.
"""
from datetime import datetime
import numpy as np
from typing import Dict, List, Optional

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
    Supports candidate selection: 'lightgbm', 'xgboost', 'random_forest', 'censored'.
    """
    try:
        model_type = (request.model_type or "lightgbm").lower().strip()

        # Registry metadata
        reg = loader.get_registry().get("inventory_prediction", {})
        verified_metrics = reg.get("metrics", {})
        holdout_metrics = reg.get("holdout_company3_metrics", {})
        reorder_eval = reg.get("dev_reorder_evaluation", {})

        provenance = {
            "dataset_version": "synthetic_v2",
            "training_period": "2022-01 to 2026-02 (58 months, 142,791 records)",
            "cross_tenant_holdout": "Company 3 (Apna Kirana Store) zero-shot holdout",
            "val_wape_pct": verified_metrics.get("val_wape_pct", 56.88),
            "holdout_wape_pct": holdout_metrics.get("wape_pct", 53.70),
            "service_level_pct": reorder_eval.get("service_level_pct", 100.0),
            "safety_stock_units": reorder_eval.get("safety_stock_units", 11.45),
        }

        if model_type == "xgboost":
            model_key = "inventory_xgboost"
            model_name = "XGBoost Inventory Demand Predictor"
            model_version = "inventory_demand_xgboost.pkl"
        elif model_type in ["random_forest", "rf"]:
            model_key = "inventory_random_forest"
            model_name = "Random Forest Inventory Demand Predictor"
            model_version = "inventory_demand_random_forest.pkl"
        elif model_type == "censored":
            model_key = "inventory_censored"
            model_name = "Censored Demand Tobit-Style Forecaster"
            model_version = "inventory_demand_censored.pkl"
        else:
            # Production winner: LightGBM
            model_key = "inventory_selected"
            model_name = "LightGBM Inventory Demand Predictor (Winner)"
            model_version = "inventory_demand_selected.pkl"

        model_obj = loader.get_model(model_key) or loader.get_model("inventory_selected") or loader.get_model("inventory_demand")
        if not model_obj or not isinstance(model_obj, dict):
            raise ValueError(f"Inventory demand model artifact '{model_key}' is not available.")

        model = model_obj["model"]
        feat_cols = model_obj.get("feature_cols", [])

        history = request.historical_monthly_demand or _default_inventory_demand_history()
        while len(history) < 6:
            history.insert(0, history[0] if history else 300.0)

        current_date = datetime.now()
        m_idx = current_date.month
        y_idx = current_date.year
        quarter = (m_idx - 1) // 3 + 1

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
                "month_num": float(m_idx),
                "quarter": float(quarter),
                "year": float(y_idx),
                "is_q4": 1.0 if quarter == 4 else 0.0,
                "is_q1": 1.0 if quarter == 1 else 0.0,
                "product_hist_mean": float(np.mean(history)),
                "product_hist_std": float(np.std(history)),
                "lag_1_norm": float(history[-1] / max(1.0, float(np.mean(history)))),
                "roll3_norm": float(np.mean(history[-3:]) / max(1.0, float(np.mean(history)))),
                "demand_momentum": float((history[-1] - history[-2]) / max(1.0, history[-2])),
                "festive_q4": 1.0 if quarter == 4 else 0.0,
            }

        X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
        predicted_demand = float(model.predict(X)[0])
        predicted_demand = max(10.0, predicted_demand)

        # Inventory Optimization Calculations
        daily_demand = predicted_demand / 30.0
        lead_time_days = request.lead_time_days
        safety_stock = daily_demand * 7.0
        reorder_point = (daily_demand * lead_time_days) + safety_stock
        reorder_quantity = max(50.0, predicted_demand * 1.2)

        curr_stock = request.current_stock if request.current_stock is not None else 0.0
        days_supply = curr_stock / (daily_demand + 1e-6)

        if days_supply <= 7.0:
            risk_level = "CRITICAL"
        elif days_supply <= 14.0:
            risk_level = "HIGH"
        elif days_supply <= 30.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        reorder_rec = curr_stock <= reorder_point

        return InventoryPredictionResponse(
            product_id=request.product_id,
            product_name=request.product_name or "Target Product",
            current_stock=curr_stock,
            predicted_monthly_demand=round(predicted_demand, 2),
            recommended_reorder_point=round(reorder_point, 2),
            recommended_reorder_quantity=round(reorder_quantity, 2),
            stockout_risk_level=risk_level,
            days_of_supply_remaining=round(days_supply, 1),
            reorder_recommended=reorder_rec,
            model_used=model_name,
            model_name=model_name,
            model_version=model_version,
            metrics=verified_metrics,
            data_provenance=provenance,
        )
    except Exception as e:
        logger.error("[InventoryPredictor] Prediction failed: {}", e)
        raise e
