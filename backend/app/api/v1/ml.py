"""
Machine Learning Predictions API Router.
Exposes endpoints for:
  - Revenue Forecasting (/revenue/predict)
  - Sales Forecasting (/sales/predict)
  - Inventory Demand Prediction (/inventory/predict)
  - Profit Prediction (/profit/predict)
  - Expense Prediction (/expense/predict)
  - Business Health Scoring (/business-health/predict)
  - Anomaly Detection (/anomaly/predict)
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import logger
from app.ml.model_loader import ModelLoader, get_model_loader
from app.ml.revenue_predictor import predict_revenue
from app.ml.sales_predictor import predict_sales
from app.ml.inventory_predictor import predict_inventory
from app.ml.profit_predictor import predict_profit
from app.ml.expense_predictor import predict_expense
from app.ml.business_health import calculate_business_health
from app.ml.anomaly_detector import detect_anomaly
from app.schemas.common import SuccessResponse
from app.schemas.ml import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    BusinessHealthRequest,
    BusinessHealthResponse,
    ExpensePredictionRequest,
    ExpensePredictionResponse,
    InventoryPredictionRequest,
    InventoryPredictionResponse,
    ProfitPredictionRequest,
    ProfitPredictionResponse,
    RevenuePredictionRequest,
    RevenuePredictionResponse,
    SalesPredictionRequest,
    SalesPredictionResponse,
)

router = APIRouter(prefix="/ml", tags=["ML Predictions"])


@router.post(
    "/revenue/predict",
    response_model=SuccessResponse[RevenuePredictionResponse],
    summary="Forecast platform / company monthly revenue",
    description=(
        "Uses trained XGBoost or SARIMA time-series models to forecast future monthly revenue.\n\n"
        "- **months_ahead**: Forecast horizon in months (1-24).\n"
        "- **model_type**: Select algorithm ('xgboost' or 'sarima').\n"
        "- **historical_revenue**: Optional custom revenue numbers to base lag calculations on."
    ),
)
def forecast_revenue_endpoint(
    payload: RevenuePredictionRequest,
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        res = predict_revenue(payload, loader)
        return SuccessResponse(data=res)
    except Exception as e:
        logger.error("[API ML] Revenue prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revenue prediction failed: {str(e)}",
        )


@router.post(
    "/sales/predict",
    response_model=SuccessResponse[SalesPredictionResponse],
    summary="Forecast product or category sales demand",
    description=(
        "Predicts upcoming units sold and total sales volume per product or category using XGBoost or LightGBM.\n\n"
        "- **entity_type**: 'product' or 'category'.\n"
        "- **model_type**: 'xgboost' or 'lightgbm'.\n"
        "- **months_ahead**: Horizon (1-12 months)."
    ),
)
def forecast_sales_endpoint(
    payload: SalesPredictionRequest,
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        res = predict_sales(payload, loader)
        return SuccessResponse(data=res)
    except Exception as e:
        logger.error("[API ML] Sales prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sales prediction failed: {str(e)}",
        )


@router.post(
    "/inventory/predict",
    response_model=SuccessResponse[InventoryPredictionResponse],
    summary="Predict inventory demand and stock reorder triggers",
    description=(
        "Estimates monthly inventory demand, calculates optimal reorder points, and evaluates stockout risk.\n\n"
        "- **current_stock**: Current available inventory units.\n"
        "- **lead_time_days**: Supplier replenishment lead time."
    ),
)
def predict_inventory_endpoint(
    payload: InventoryPredictionRequest,
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        res = predict_inventory(payload, loader)
        return SuccessResponse(data=res)
    except Exception as e:
        logger.error("[API ML] Inventory prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inventory prediction failed: {str(e)}",
        )


@router.post(
    "/profit/predict",
    response_model=SuccessResponse[ProfitPredictionResponse],
    summary="Predict gross & net profit margins",
    description=(
        "Predicts upcoming monthly profit performance, profit margin percentage, and margin efficiency status.\n\n"
        "- **historical_profits**: Optional list of recent net profit figures.\n"
        "- **projected_revenue**: Estimated upcoming revenue base."
    ),
)
def predict_profit_endpoint(
    payload: ProfitPredictionRequest,
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        res = predict_profit(payload, loader)
        return SuccessResponse(data=res)
    except Exception as e:
        logger.error("[API ML] Profit prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profit prediction failed: {str(e)}",
        )


@router.post(
    "/expense/predict",
    response_model=SuccessResponse[ExpensePredictionResponse],
    summary="Forecast operating expenses and flag spending risks",
    description=(
        "Predicts future operational expenses per category and generates expense anomaly surge alerts.\n\n"
        "- **category**: Expense category (e.g., Rent, Salaries, Marketing).\n"
        "- **model_type**: 'xgboost' or 'linear_regression'."
    ),
)
def predict_expense_endpoint(
    payload: ExpensePredictionRequest,
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        res = predict_expense(payload, loader)
        return SuccessResponse(data=res)
    except Exception as e:
        logger.error("[API ML] Expense prediction failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Expense prediction failed: {str(e)}",
        )


@router.post(
    "/business-health/predict",
    response_model=SuccessResponse[BusinessHealthResponse],
    summary="Calculate composite Business Health Score (0-100)",
    description=(
        "Evaluates 5 core financial KPIs to calculate overall Business Health Index, letter grade (A-F), and actionable advice.\n\n"
        "- **revenue_growth**: Growth rate ratio.\n"
        "- **profit_margin**: Net profit margin ratio.\n"
        "- **expense_control**: Operational expense efficiency index.\n"
        "- **inventory_turnover**: Inventory turnover ratio.\n"
        "- **payment_collection**: Receivable collection efficiency."
    ),
)
def calculate_business_health_endpoint(
    payload: BusinessHealthRequest,
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        res = calculate_business_health(payload, loader)
        return SuccessResponse(data=res)
    except Exception as e:
        logger.error("[API ML] Business health score calculation failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Business health score calculation failed: {str(e)}",
        )


@router.post(
    "/anomaly/predict",
    response_model=SuccessResponse[AnomalyDetectionResponse],
    summary="Detect transaction & invoice anomalies",
    description=(
        "Uses trained Isolation Forest model to detect suspicious invoices, price anomalies, or uncharacteristic transactions.\n\n"
        "- **net_amount**: Transaction net value.\n"
        "- **discount_pct**: Applied discount percentage."
    ),
)
def detect_anomaly_endpoint(
    payload: AnomalyDetectionRequest,
    loader: ModelLoader = Depends(get_model_loader),
):
    try:
        res = detect_anomaly(payload, loader)
        return SuccessResponse(data=res)
    except Exception as e:
        logger.error("[API ML] Anomaly detection failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}",
        )
