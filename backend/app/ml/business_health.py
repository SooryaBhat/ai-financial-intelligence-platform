"""
Business Health Score Service.
Calculates overall business health index (0-100), letter grade, risk tier, and sub-score metrics.
"""
from typing import Dict, List, Any

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
    Calculate composite Business Health Score and sub-component metrics.
    """
    try:
        pipeline_obj = loader.get_model("health_score_pipeline")
        config_obj = loader.get_meta("health_config")

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

        if pipeline_obj and isinstance(pipeline_obj, dict):
            weights = pipeline_obj.get("weights", weights)
            kpi_ranges = pipeline_obj.get("kpi_ranges", kpi_ranges)
        elif config_obj and isinstance(config_obj, dict):
            weights = config_obj.get("weights", weights)
            kpi_ranges = config_obj.get("kpi_ranges", kpi_ranges)

        raw_kpis = {
            "revenue_growth": request.revenue_growth,
            "profit_margin": request.profit_margin,
            "expense_control": request.expense_control,
            "inventory_turnover": request.inventory_turnover,
            "payment_collection": request.payment_collection,
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
        if total_health_score >= 85.0:
            grade = "A"
            risk = "LOW_RISK"
        elif total_health_score >= 70.0:
            grade = "B"
            risk = "LOW_RISK"
        elif total_health_score >= 55.0:
            grade = "C"
            risk = "MODERATE_RISK"
        elif total_health_score >= 40.0:
            grade = "D"
            risk = "HIGH_RISK"
        else:
            grade = "F"
            risk = "CRITICAL_RISK"

        # Actionable Recommendations
        recs: List[str] = []
        if sub_scores.get("score_revenue_growth", 0) < 60:
            recs.append("Boost revenue growth through expansion of top-performing product categories.")
        if sub_scores.get("score_profit_margin", 0) < 60:
            recs.append("Optimize product pricing and negotiate supplier discounts to improve profit margins.")
        if sub_scores.get("score_expense_control", 0) < 60:
            recs.append("Conduct an expense audit to curb recurring non-essential operational costs.")
        if sub_scores.get("score_inventory_turnover", 0) < 60:
            recs.append("Implement automated stock reorder points to reduce holding costs and dead stock.")
        if sub_scores.get("score_payment_collection", 0) < 60:
            recs.append("Tighten credit terms and send automated invoice reminders to accelerate cash collection.")

        if not recs:
            recs.append("Maintain current operational efficiency and monitor financial indicators monthly.")

        return BusinessHealthResponse(
            health_score=total_health_score,
            health_grade=grade,
            risk_rating=risk,
            sub_scores=sub_scores,
            weights=weights,
            recommendations=recs,
        )
    except Exception as e:
        logger.error("[BusinessHealth] Health score calculation failed: {}", e)
        raise e
