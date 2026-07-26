"""
Transaction Anomaly Detection Service.
Uses trained Isolation Forest & Scaler pipeline to flag anomalous transactions/invoices.
"""
from datetime import datetime
import numpy as np
from typing import Dict, Any

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
)


def detect_anomaly(
    request: AnomalyDetectionRequest,
    loader: ModelLoader,
) -> AnomalyDetectionResponse:
    """
    Detect transaction anomalies using trained Isolation Forest pipeline.
    """
    try:
        model_obj = loader.get_model("anomaly_detection")
        if not model_obj or not isinstance(model_obj, dict):
            raise ValueError("Anomaly detection model artifact is not available.")

        model = model_obj["model"]
        scaler = model_obj["scaler"]
        feat_cols = model_obj["feature_cols"]

        now = datetime.now()
        day_of_week = request.day_of_week if request.day_of_week is not None else now.weekday()
        is_weekend = request.is_weekend if request.is_weekend is not None else (1 if day_of_week >= 5 else 0)
        month = request.month if request.month is not None else now.month

        roll28_mean = request.roll28_mean if request.roll28_mean is not None else 18500.0
        roll28_std = request.roll28_std if request.roll28_std is not None else 6200.0
        z_score = request.amount_z_rolling if request.amount_z_rolling is not None else (
            (request.net_amount - roll28_mean) / (roll28_std + 1e-6)
        )

        feat_dict = {
            "net_amount": float(request.net_amount),
            "discount_pct": float(request.discount_pct),
            "day_of_week": float(day_of_week),
            "is_weekend": float(is_weekend),
            "month": float(month),
            "status_enc": float(request.status_enc),
            "roll28_mean": float(roll28_mean),
            "roll28_std": float(roll28_std),
            "amount_z_rolling": float(z_score),
        }

        X_raw = np.array([[feat_dict.get(col, 0.0) for col in feat_cols]], dtype=np.float32)
        X_scaled = scaler.transform(X_raw)

        pred_label = int(model.predict(X_scaled)[0])  # -1 = anomaly, 1 = normal
        decision_score = float(model.decision_function(X_scaled)[0])

        is_anomaly = (pred_label == -1) or (z_score > 3.5) or (request.discount_pct > 50.0)

        if decision_score < -0.12 or z_score > 4.0 or request.discount_pct > 60.0:
            severity = "CRITICAL"
        elif decision_score < -0.05 or z_score > 3.0:
            severity = "HIGH"
        elif decision_score < 0.00 or z_score > 2.0:
            severity = "MEDIUM"
        elif is_anomaly:
            severity = "LOW"
        else:
            severity = "NORMAL"

        confidence = min(99.9, max(50.0, 100.0 * (1.0 - abs(decision_score))))

        reasons = []
        if z_score > 3.0:
            reasons.append(f"Net amount ({request.net_amount:,.2f}) significantly deviates from 28-day baseline (Z={z_score:.2f}).")
        if request.discount_pct > 40.0:
            reasons.append(f"High discount applied ({request.discount_pct:.1f}% exceeds 40% threshold).")
        if is_anomaly and not reasons:
            reasons.append("Unusual multi-variable transaction pattern detected by Isolation Forest model.")
        if not reasons:
            reasons.append("Transaction characteristics match normal historical behavior.")

        reason_str = " ".join(reasons)

        return AnomalyDetectionResponse(
            is_anomaly=is_anomaly,
            anomaly_score=round(decision_score, 4),
            severity=severity,
            confidence=round(confidence, 1),
            reason=reason_str,
        )
    except Exception as e:
        logger.error("[AnomalyDetector] Detection failed: {}", e)
        raise e
