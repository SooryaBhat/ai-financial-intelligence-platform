"""
Revenue Forecasting Service.
Uses trained XGBoost or SARIMA model to forecast monthly revenues.
"""
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    RevenueForecastItem,
    RevenuePredictionRequest,
    RevenuePredictionResponse,
)


def _default_historical_revenue() -> List[float]:
    """Default platform historical monthly revenue baseline (in INR/USD)."""
    return [
        17614888.57, 20425539.38, 17583044.84, 18827104.21, 25109568.59, 21361444.49,
        22150000.00, 23400000.00, 21800000.00, 24500000.00, 26000000.00, 28500000.00,
    ]


def predict_revenue(
    request: RevenuePredictionRequest,
    loader: ModelLoader,
) -> RevenuePredictionResponse:
    """
    Generate multi-month revenue forecasts using trained ML models.
    """
    try:
        model_type = request.model_type.lower()
        months_ahead = request.months_ahead
        history = request.historical_revenue or _default_historical_revenue()

        # Ensure history has at least 12 months for full lag computation
        while len(history) < 12:
            history.insert(0, history[0] if history else 15000000.0)

        predictions: List[RevenueForecastItem] = []
        current_date = datetime.now()
        start_year = current_date.year
        start_month = current_date.month

        if model_type == "sarima":
            sarima_model = loader.get_model("revenue_sarima")
            if sarima_model is not None:
                # Forecast directly using statsmodels SARIMA
                forecast_vals = sarima_model.forecast(steps=months_ahead)
                for i in range(months_ahead):
                    m_idx = (start_month + i - 1) % 12 + 1
                    y_idx = start_year + (start_month + i - 1) // 12
                    target_date = f"{y_idx:04d}-{m_idx:02d}-28"
                    pred_val = float(forecast_vals.iloc[i] if hasattr(forecast_vals, 'iloc') else forecast_vals[i])
                    pred_val = max(1000.0, pred_val)
                    predictions.append(
                        RevenueForecastItem(
                            month=target_date,
                            predicted_revenue=round(pred_val, 2),
                            confidence_lower=round(pred_val * 0.90, 2),
                            confidence_upper=round(pred_val * 1.10, 2),
                        )
                    )
                model_name = "SARIMA(1,1,1)(1,1,0,12)"
            else:
                logger.warning("[RevenuePredictor] SARIMA model not found, falling back to XGBoost")
                model_type = "xgboost"

        if model_type != "sarima":
            xgb_obj = loader.get_model("revenue_xgboost")
            if not xgb_obj or not isinstance(xgb_obj, dict):
                raise ValueError("XGBoost revenue model artifact is not loaded correctly.")

            xgb_model = xgb_obj["model"]
            feat_cols = xgb_obj["feature_cols"]

            curr_history = list(history)
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
                        "lag_6": curr_history[-6],
                        "lag_12": curr_history[-12],
                        "roll3_mean": float(np.mean(curr_history[-3:])),
                        "roll6_mean": float(np.mean(curr_history[-6:])),
                        "month_num": float(m_idx),
                        "quarter": float(quarter),
                    }

                X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
                pred_val = float(xgb_model.predict(X)[0])
                pred_val = max(1000.0, pred_val)

                predictions.append(
                    RevenueForecastItem(
                        month=target_date,
                        predicted_revenue=round(pred_val, 2),
                        confidence_lower=round(pred_val * 0.92, 2),
                        confidence_upper=round(pred_val * 1.08, 2),
                    )
                )
                curr_history.append(pred_val)

            model_name = "XGBoost Revenue Regressor"

        total_rev = sum(p.predicted_revenue for p in predictions)
        avg_rev = total_rev / len(predictions) if predictions else 0.0

        if len(predictions) >= 2:
            first_half = np.mean([p.predicted_revenue for p in predictions[:len(predictions)//2]])
            second_half = np.mean([p.predicted_revenue for p in predictions[len(predictions)//2:]])
            diff = (second_half - first_half) / (first_half + 1e-8)
            trend = "UPWARD" if diff > 0.02 else ("DOWNWARD" if diff < -0.02 else "STABLE")
        else:
            trend = "STABLE"

        return RevenuePredictionResponse(
            model_used=model_name,
            forecast_period_months=months_ahead,
            predictions=predictions,
            total_projected_revenue=round(total_rev, 2),
            average_monthly_revenue=round(avg_rev, 2),
            growth_trend=trend,
        )
    except Exception as e:
        logger.error("[RevenuePredictor] Prediction failed: {}", e)
        raise e
