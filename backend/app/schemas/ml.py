"""
Pydantic v2 schemas for Machine Learning prediction endpoints.
Provides structured request and response models with validation for:
  - Revenue Forecasting
  - Sales Forecasting
  - Inventory Demand Prediction
  - Profit Prediction
  - Expense Prediction
  - Business Health Scoring
  - Anomaly Detection
"""
from typing import Any, Dict, List, Optional
from pydantic import Field
from app.schemas.common import AppBaseModel


# ── 1. Revenue Forecasting ────────────────────────────────────

class RevenuePredictionRequest(AppBaseModel):
    months_ahead: int = Field(
        default=6,
        ge=1,
        le=24,
        description="Number of months to forecast into the future (1-24)"
    )
    model_type: str = Field(
        default="xgboost",
        description="ML model engine: 'xgboost' or 'sarima'"
    )
    historical_revenue: Optional[List[float]] = Field(
        default=None,
        description="Optional recent monthly revenue numbers (min 12 months) to compute lags dynamically"
    )
    custom_features: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional raw feature map ('lag_1', 'lag_2', 'lag_3', 'lag_6', 'lag_12', 'roll3_mean', etc.)"
    )


class RevenueForecastItem(AppBaseModel):
    month: str = Field(..., description="Target forecast month (YYYY-MM-DD)")
    predicted_revenue: float = Field(..., description="Forecasted revenue amount in base currency")
    confidence_lower: float = Field(..., description="Lower 95% confidence interval boundary")
    confidence_upper: float = Field(..., description="Upper 95% confidence interval boundary")


class RevenuePredictionResponse(AppBaseModel):
    model_used: str = Field(..., description="Model engine used for prediction")
    forecast_period_months: int = Field(..., description="Total months forecasted")
    predictions: List[RevenueForecastItem]
    total_projected_revenue: float = Field(..., description="Sum of forecasted revenues across period")
    average_monthly_revenue: float = Field(..., description="Average projected monthly revenue")
    growth_trend: str = Field(..., description="Trend indicator: 'UPWARD', 'STABLE', or 'DOWNWARD'")


# ── 2. Sales Forecasting ──────────────────────────────────────

class SalesPredictionRequest(AppBaseModel):
    entity_type: str = Field(
        default="product",
        description="Forecast entity type: 'product' or 'category'"
    )
    entity_id: Optional[str] = Field(
        default=None,
        description="Optional Product or Category identifier"
    )
    model_type: str = Field(
        default="xgboost",
        description="ML model engine: 'xgboost' or 'lightgbm'"
    )
    months_ahead: int = Field(default=3, ge=1, le=12, description="Months ahead to forecast (1-12)")
    historical_sales: Optional[List[float]] = Field(
        default=None,
        description="Optional historical monthly sales volume/units"
    )
    custom_features: Optional[Dict[str, float]] = Field(default=None)


class SalesForecastItem(AppBaseModel):
    month: str
    predicted_units_sold: float
    predicted_sales_amount: float


class SalesPredictionResponse(AppBaseModel):
    entity_type: str
    entity_id: Optional[str] = None
    model_used: str
    predictions: List[SalesForecastItem]
    total_predicted_units: float
    total_predicted_amount: float


# ── 3. Inventory Prediction ───────────────────────────────────

class InventoryPredictionRequest(AppBaseModel):
    product_id: Optional[str] = Field(default=None, description="Product UUID or SKU code")
    product_name: Optional[str] = Field(default=None, description="Product display name")
    current_stock: float = Field(..., ge=0, description="Current warehouse stock quantity")
    unit_cost: float = Field(default=10.0, ge=0, description="Cost per unit")
    lead_time_days: int = Field(default=14, ge=1, le=90, description="Supplier lead time in days")
    historical_monthly_demand: Optional[List[float]] = Field(default=None)
    custom_features: Optional[Dict[str, float]] = Field(default=None)


class InventoryPredictionResponse(AppBaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    current_stock: float
    predicted_monthly_demand: float
    recommended_reorder_point: float
    recommended_reorder_quantity: float
    stockout_risk_level: str = Field(..., description="Risk category: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'")
    days_of_supply_remaining: float
    reorder_recommended: bool


# ── 4. Profit Prediction ──────────────────────────────────────

class ProfitPredictionRequest(AppBaseModel):
    historical_profits: Optional[List[float]] = Field(default=None, description="Recent monthly net profit values")
    historical_revenues: Optional[List[float]] = Field(default=None, description="Recent monthly revenue values")
    projected_revenue: Optional[float] = Field(default=None, description="Estimated upcoming monthly revenue")
    custom_features: Optional[Dict[str, float]] = Field(default=None)


class ProfitPredictionResponse(AppBaseModel):
    predicted_profit: float
    predicted_profit_margin_pct: float
    profitability_status: str = Field(..., description="'HIGHLY_PROFITABLE', 'MODERATELY_PROFITABLE', 'LOW_MARGIN', 'UNPROFITABLE'")
    confidence_score: float
    influencing_factors: Dict[str, Any]


# ── 5. Expense Prediction ─────────────────────────────────────

class ExpensePredictionRequest(AppBaseModel):
    category: Optional[str] = Field(
        default=None,
        description="Expense category (e.g., Rent, Salaries, Utilities, Marketing, IT & Software, Travel)"
    )
    model_type: str = Field(
        default="xgboost",
        description="ML model engine: 'xgboost' or 'linear_regression'"
    )
    months_ahead: int = Field(default=1, ge=1, le=12)
    historical_expenses: Optional[List[float]] = Field(default=None)
    custom_features: Optional[Dict[str, float]] = Field(default=None)


class ExpensePredictionResponse(AppBaseModel):
    model_used: str
    category: Optional[str] = None
    predicted_expense: float
    predicted_transaction_count: int
    expense_risk_alert: str = Field(..., description="'NORMAL', 'ELEVATED', or 'HIGH_ANOMALOUS_EXPENSE'")
    category_breakdown: Optional[Dict[str, float]] = None


# ── 6. Business Health Score ──────────────────────────────────

class BusinessHealthRequest(AppBaseModel):
    revenue_growth: float = Field(default=0.15, description="Revenue growth rate (e.g. 0.15 for +15%)")
    profit_margin: float = Field(default=0.20, description="Net profit margin ratio (e.g. 0.20 for 20%)")
    expense_control: float = Field(default=0.82, description="Expense efficiency index (0.0 to 1.0, e.g. 0.82)")
    inventory_turnover: float = Field(default=4.5, description="Inventory turnover ratio (e.g. 4.5)")
    payment_collection: float = Field(default=0.90, description="Payment collection efficiency (0.0 to 1.0, e.g. 0.90)")


class BusinessHealthResponse(AppBaseModel):
    health_score: float = Field(..., description="Overall Business Health Score (0.0 - 100.0)")
    health_grade: str = Field(..., description="Health Letter Grade: 'A', 'B', 'C', 'D', 'F'")
    risk_rating: str = Field(..., description="Risk tier: 'LOW_RISK', 'MODERATE_RISK', 'HIGH_RISK', 'CRITICAL_RISK'")
    sub_scores: Dict[str, float] = Field(..., description="Component sub-scores (0-100 scale)")
    weights: Dict[str, float] = Field(..., description="KPI weighting configuration used")
    recommendations: List[str] = Field(..., description="Actionable insights to optimize financial health")


# ── 7. Anomaly Detection ──────────────────────────────────────

class AnomalyDetectionRequest(AppBaseModel):
    net_amount: float = Field(..., description="Transaction net amount")
    discount_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Discount percentage applied")
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    is_weekend: Optional[int] = Field(default=None, ge=0, le=1, description="1 if weekend, else 0")
    month: Optional[int] = Field(default=None, ge=1, le=12, description="Month number (1-12)")
    status_enc: int = Field(default=0, description="Encoded transaction status code")
    roll28_mean: Optional[float] = Field(default=None, description="28-day rolling average transaction amount")
    roll28_std: Optional[float] = Field(default=None, description="28-day rolling standard deviation")
    amount_z_rolling: Optional[float] = Field(default=None, description="Amount Z-score relative to rolling window")


class AnomalyDetectionResponse(AppBaseModel):
    is_anomaly: bool = Field(..., description="True if transaction is flagged as an anomaly")
    anomaly_score: float = Field(..., description="Raw decision score from Isolation Forest (lower = higher anomaly)")
    severity: str = Field(..., description="'NORMAL', 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'")
    confidence: float = Field(..., description="Confidence percentage (0-100%)")
    reason: str = Field(..., description="Detailed diagnostic explanation")
