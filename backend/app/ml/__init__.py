"""
Machine Learning Service Layer.
Exposes ModelLoader and predictor services for high-performance model inference.
"""
from app.ml.model_loader import model_loader, get_model_loader
from app.ml.revenue_predictor import predict_revenue
from app.ml.sales_predictor import predict_sales
from app.ml.inventory_predictor import predict_inventory
from app.ml.profit_predictor import predict_profit
from app.ml.expense_predictor import predict_expense
from app.ml.business_health import calculate_business_health
from app.ml.anomaly_detector import detect_anomaly

__all__ = [
    "model_loader",
    "get_model_loader",
    "predict_revenue",
    "predict_sales",
    "predict_inventory",
    "predict_profit",
    "predict_expense",
    "calculate_business_health",
    "detect_anomaly",
]
