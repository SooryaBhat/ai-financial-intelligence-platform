"""
Business Health Score Service.
Calculates overall business health index (0-100), letter grade, risk tier,
deterministic sub-score metrics, and forward transition trajectory.
"""
from typing import Dict, List, Any, Optional
import numpy as np

from app.core.logging import logger
from app.ml.model_loader import ModelLoader
from app.schemas.ml import (
    BusinessHealthRequest,
    BusinessHealthResponse,
)


def _scale_kpi(val: float, min_v: float, max_v: float) -> float:
    """MinMax scale value to 0-100 percentage range."""
    if max_v <= min_v:
        return 50.0
    norm = (val - min_v) / (max_v - min_v)
    return float(min(100.0, max(0.0, norm * 100.0)))


def calculate_business_health(
    request: BusinessHealthRequest,
    loader: ModelLoader,
) -> BusinessHealthResponse:
    """
    Calculate composite Business Health Score, sub-component metrics,
    and forward transition projection.
    """
    try:
        pipeline_obj = loader.get_model("health_score_selected") or loader.get_model("health_score_pipeline")
        config_obj = loader.get_meta("health_config")

        # Registry metadata
        reg = loader.get_registry().get("business_health_score", {})
        verified_metrics = reg.get("metrics", {})
        holdout_metrics = reg.get("holdout_company3_metrics", {})

        provenance = {
            "dataset_version": "synthetic_v2",
            "training_period": "2022-01 to 2026-02 (58 months, 142,791 records)",
            "cross_tenant_holdout": "Company 3 (Apna Kirana Store) zero-shot holdout",
            "val_mae_points": verified_metrics.get("val_mae", 4.75),
            "holdout_mae_points": holdout_metrics.get("mae", 2.92),
            "scorecard_engine": "Transparent Weighted KPI Scorecard (0-100)",
        }

        weights = {
            "revenue_growth": 0.25,
            "profit_margin": 0.25,
            "expense_control": 0.20,
            "inventory_turnover": 0.15,
            "payment_collection": 0.15,
        }
        kpi_ranges = {
            "revenue_growth": [-0.50, 1.00],
            "profit_margin": [-0.20, 0.40],
            "expense_control": [0.00, 1.00],
            "inventory_turnover": [0.00, 10.00],
            "payment_collection": [0.00, 1.00],
        }

        transition_model = None
        feature_cols = []
        selected_model_name = "TransparentKPIScorecard + Linear_Regression"

        if pipeline_obj and isinstance(pipeline_obj, dict):
            weights = pipeline_obj.get("weights", weights)
            kpi_ranges = pipeline_obj.get("kpi_ranges", kpi_ranges)
            transition_model = pipeline_obj.get("transition_model")
            feature_cols = pipeline_obj.get("feature_cols", [])
            selected_model_name = pipeline_obj.get("selected_model", selected_model_name)
        elif config_obj and isinstance(config_obj, dict):
            weights = config_obj.get("weights", weights)
            kpi_ranges = config_obj.get("kpi_ranges", kpi_ranges)

        raw_kpis = {
            "revenue_growth": request.revenue_growth if request.revenue_growth is not None else 0.15,
            "profit_margin": request.profit_margin if request.profit_margin is not None else 0.20,
            "expense_control": request.expense_control if request.expense_control is not None else 0.82,
            "inventory_turnover": request.inventory_turnover if request.inventory_turnover is not None else 4.5,
            "payment_collection": request.payment_collection if request.payment_collection is not None else 0.90,
        }

        sub_scores: Dict[str, float] = {}
        weighted_sum = 0.0

        for kpi, val in raw_kpis.items():
            r = kpi_ranges.get(kpi, [0.0, 1.0])
            score = _scale_kpi(val, r[0], r[1])
            sub_scores[f"score_{kpi}"] = round(score, 2)
            w = weights.get(kpi, 0.20)
            weighted_sum += score * w

        total_health_score = round(float(weighted_sum), 1)

        # Determine Letter Grade & Risk Tier
        if total_health_score >= 80.0:
            grade = "A"
            risk = "LOW_RISK"
        elif total_health_score >= 65.0:
            grade = "B"
            risk = "LOW_RISK"
        elif total_health_score >= 50.0:
            grade = "C"
            risk = "MODERATE_RISK"
        elif total_health_score >= 35.0:
            grade = "D"
            risk = "HIGH_RISK"
        else:
            grade = "F"
            risk = "CRITICAL_RISK"

        # Forward transition prediction (next month projected health score)
        projected_next_score = None
        if transition_model is not None and feature_cols:
            try:
                feat_dict = {
                    "health_score": total_health_score,
                    "health_score_lag1": total_health_score,
                    "health_score_roll3": total_health_score,
                    "revenue_growth": raw_kpis["revenue_growth"],
                    "profit_margin": raw_kpis["profit_margin"],
                    "expense_control": raw_kpis["expense_control"],
                    "inventory_turnover": raw_kpis["inventory_turnover"],
                    "payment_collection": raw_kpis["payment_collection"],
                    "month_num": 10.0,
                    "quarter": 4.0,
                }
                X = np.array([[feat_dict.get(col, 0.0) for col in feature_cols]], dtype=np.float32)
                pred_next = float(transition_model.predict(X)[0])
                projected_next_score = round(float(np.clip(pred_next, 0.0, 100.0)), 1)
            except Exception as te:
                logger.warning("[BusinessHealth] Transition prediction failed: {}", te)

        # Actionable Recommendations
        recs: List[str] = []
        if sub_scores.get("score_revenue_growth", 0) < 60:
            recs.append("Boost revenue growth through expansion of top-performing product categories.")
        if sub_scores.get("score_profit_margin", 0) < 60:
            recs.append("Optimize product pricing and negotiate supplier discounts to improve profit margins.")
        if sub_scores.get("score_expense_control", 0) < 60:
            recs.append("Conduct an expense audit to curb recurring non-essential operational costs.")
        if sub_scores.get("score_inventory_turnover", 0) < 60:
            recs.append("Liquidate slow-moving SKU inventory to release working capital.")
        if sub_scores.get("score_payment_collection", 0) < 60:
            recs.append("Implement automated payment reminders to shorten the cash collection cycle.")
        if not recs:
            recs.append("Excellent operational performance across all 5 key financial health pillars.")

        return BusinessHealthResponse(
            health_score=total_health_score,
            health_grade=grade,
            risk_rating=risk,
            sub_scores=sub_scores,
            weights=weights,
            recommendations=recs,
            projected_next_month_health_score=projected_next_score,
            model_used=f"TransparentKPIScorecard ({grade} Grade)",
            model_name=selected_model_name,
            model_version="health_score_selected.pkl",
            metrics=verified_metrics,
            data_provenance=provenance,
        )
    except Exception as e:
        logger.error("[BusinessHealth] Health score calculation failed: {}", e)
        raise e
