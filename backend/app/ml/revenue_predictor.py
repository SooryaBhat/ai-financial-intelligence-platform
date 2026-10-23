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
    """Default platform historical monthly revenue baseline across Indian retail stores (~Rs. 250k-350k/mo)."""
    return [
        253538.11, 225239.65, 255930.89, 254989.03, 264565.76, 264128.18,
        254534.83, 261845.50, 256036.27, 388987.42, 312945.67, 337562.33,
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
            history.insert(0, history[0] if history else 250000.0)

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
            # Resolve model artifact by algorithm or default to validation-selected
            if model_type == "aagf":
                model_obj = loader.get_model("revenue_aagf") or loader.get_model("revenue_selected")
                model_name = "ALLADIN Adaptive Global Forecaster (AAGF)"
            elif model_type in ["linear", "linear_regression"]:
                model_obj = loader.get_model("revenue_linear_regression")
                model_name = "Linear Regression Revenue Predictor"
            elif model_type == "xgboost":
                model_obj = loader.get_model("revenue_xgboost")
                model_name = "XGBoost Revenue Predictor"
            else:
                model_obj = loader.get_model("revenue_selected") or loader.get_model("revenue_aagf") or loader.get_model("revenue_xgboost")
                algo = model_obj.get("algorithm", "Selected") if model_obj else "Selected"
                model_name = f"ALLADIN Selected Forecaster ({algo})"

            if not model_obj or not isinstance(model_obj, dict):
                model_obj = loader.get_model("revenue_xgboost")
                model_name = "Revenue Predictor (Fallback)"

            if not model_obj or not isinstance(model_obj, dict):
                raise ValueError("Revenue model artifact is not loaded correctly.")

            model = model_obj["model"]
            feat_cols = model_obj["feature_cols"]

            curr_history = list(history)
            for i in range(months_ahead):
                m_idx = (start_month + i - 1) % 12 + 1
                y_idx = start_year + (start_month + i - 1) // 12
                quarter = (m_idx - 1) // 3 + 1
                target_date = f"{y_idx:04d}-{m_idx:02d}-28"

                if request.custom_features:
                    feat_dict = dict(request.custom_features)
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

                # Predict via DataFrame if AAGF/pipeline, or ndarray if sklearn/xgb
                if hasattr(model, "weights") or hasattr(model, "trend_anchor"):
                    feat_df = pd.DataFrame([feat_dict])
                    pred_val = float(model.predict(feat_df)[0])
                else:
                    X = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
                    pred_val = float(model.predict(X)[0])

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
