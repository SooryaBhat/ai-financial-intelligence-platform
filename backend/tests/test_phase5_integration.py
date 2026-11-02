"""
Phase 5 Comprehensive Integration & Regression Test Suite for ALLADIN ML.
Validates:
1. Canonical model loading & registry integrity
2. End-to-end inference across all 7 ML pipelines
3. Genuine candidate model-selection (different algorithms execute genuinely)
4. Input validation & clear error responses
5. Safe fallback behavior
6. Response schema compliance & data provenance metadata
7. Tenant isolation & security
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.ml.model_loader import get_model_loader
from app.schemas.ml import (
    RevenuePredictionRequest,
    SalesPredictionRequest,
    InventoryPredictionRequest,
    ProfitPredictionRequest,
    ExpensePredictionRequest,
    BusinessHealthRequest,
    AnomalyDetectionRequest,
)
from app.ml.revenue_predictor import predict_revenue
from app.ml.sales_predictor import predict_sales
from app.ml.inventory_predictor import predict_inventory
from app.ml.profit_predictor import predict_profit
from app.ml.expense_predictor import predict_expense
from app.ml.business_health import calculate_business_health
from app.ml.anomaly_detector import detect_anomaly


@pytest.fixture(scope="session")
def loader():
    """Retrieve initialized ModelLoader singleton."""
    return get_model_loader()


# ── 1. ModelLoader & Canonical Registry Verification ──────────────────────

def test_canonical_model_loading(loader):
    """Verify that all 7 canonical selected models and candidate models are active."""
    assert loader.is_loaded, "ModelLoader should be initialized"

    canonical_keys = [
        "revenue_selected",
        "sales_selected",
        "inventory_selected",
        "profit_selected",
        "expense_selected",
        "health_score_selected",
        "anomaly_selected",
    ]
    for key in canonical_keys:
        model_obj = loader.get_model(key)
        assert model_obj is not None, f"Canonical model '{key}' failed to load"


def test_registry_metadata_integrity(loader):
    """Verify that the model registry contains all 7 pipelines with verified metrics."""
    reg = loader.get_registry()
    assert isinstance(reg, dict)
    expected_pipelines = [
        "revenue_forecasting",
        "sales_forecasting",
        "inventory_prediction",
        "profit_prediction",
        "expense_prediction",
        "business_health_score",
        "anomaly_detection",
    ]
    for p in expected_pipelines:
        assert p in reg, f"Pipeline '{p}' missing from canonical registry"
        pipe_info = reg[p]
        assert pipe_info.get("artifact_exists") is True, f"Artifact for '{p}' does not exist"
        assert "metrics" in pipe_info, f"Verified metrics missing for '{p}'"


# ── 2. Pipeline 1: Revenue Forecasting ─────────────────────────────────────

def test_pipeline1_revenue_candidates(loader):
    """Test genuine candidate execution for Revenue Forecasting."""
    # AAGF Winner
    req_aagf = RevenuePredictionRequest(months_ahead=6, model_type="aagf")
    res_aagf = predict_revenue(req_aagf, loader)
    assert res_aagf.forecast_period_months == 6
    assert len(res_aagf.predictions) == 6
    assert res_aagf.total_projected_revenue > 0
    assert "AAGF" in res_aagf.model_name
    assert res_aagf.data_provenance is not None

    # XGBoost
    req_xgb = RevenuePredictionRequest(months_ahead=6, model_type="xgboost")
    res_xgb = predict_revenue(req_xgb, loader)
    assert "XGBoost" in res_xgb.model_name

    # SARIMA
    req_sarima = RevenuePredictionRequest(months_ahead=6, model_type="sarima")
    res_sarima = predict_revenue(req_sarima, loader)
    assert "SARIMA" in res_sarima.model_name

    # Linear Regression
    req_lr = RevenuePredictionRequest(months_ahead=6, model_type="linear_regression")
    res_lr = predict_revenue(req_lr, loader)
    assert "Linear Regression" in res_lr.model_name

    # Confirm genuine algorithmic differentiation: AAGF vs Linear Regression
    assert res_aagf.total_projected_revenue != res_lr.total_projected_revenue


# ── 3. Pipeline 2: Sales Forecasting ───────────────────────────────────────

def test_pipeline2_sales_candidates(loader):
    """Test genuine candidate execution for Sales Demand Forecasting."""
    # Product Profile Forecaster (Winner)
    req_prof = SalesPredictionRequest(entity_type="product", model_type="product_profile", months_ahead=3)
    res_prof = predict_sales(req_prof, loader)
    assert len(res_prof.predictions) == 3
    assert res_prof.total_predicted_units > 0
    assert "Product Profile" in res_prof.model_name

    # AAGF SKU
    req_aagf = SalesPredictionRequest(entity_type="product", model_type="aagf", months_ahead=3)
    res_aagf = predict_sales(req_aagf, loader)
    assert "AAGF" in res_aagf.model_name

    # LightGBM
    req_lgb = SalesPredictionRequest(entity_type="product", model_type="lightgbm", months_ahead=3)
    res_lgb = predict_sales(req_lgb, loader)
    assert "LightGBM" in res_lgb.model_name

    # Category Level XGBoost
    req_cat = SalesPredictionRequest(entity_type="category", model_type="xgboost", months_ahead=3)
    res_cat = predict_sales(req_cat, loader)
    assert "Category" in res_cat.model_name


# ── 4. Pipeline 3: Inventory Optimization ──────────────────────────────────

def test_pipeline3_inventory_candidates(loader):
    """Test genuine candidate execution for Inventory Demand & Reorder."""
    # LightGBM (Winner)
    req_lgb = InventoryPredictionRequest(model_type="lightgbm", current_stock=20, unit_cost=100.0, lead_time_days=14)
    res_lgb = predict_inventory(req_lgb, loader)
    assert res_lgb.predicted_monthly_demand > 0
    assert res_lgb.recommended_reorder_point > 0
    assert res_lgb.days_of_supply_remaining > 0
    assert "LightGBM" in res_lgb.model_name

    # XGBoost
    req_xgb = InventoryPredictionRequest(model_type="xgboost", current_stock=20, unit_cost=100.0, lead_time_days=14)
    res_xgb = predict_inventory(req_xgb, loader)
    assert "XGBoost" in res_xgb.model_name

    # Random Forest
    req_rf = InventoryPredictionRequest(model_type="random_forest", current_stock=20, unit_cost=100.0, lead_time_days=14)
    res_rf = predict_inventory(req_rf, loader)
    assert "Random Forest" in res_rf.model_name

    # Safe null stock handling
    req_null = InventoryPredictionRequest(model_type="lightgbm", current_stock=None)
    res_null = predict_inventory(req_null, loader)
    assert res_null.current_stock == 0.0
    assert res_null.reorder_recommended is True


# ── 5. Pipeline 4: Profit Prediction ───────────────────────────────────────

def test_pipeline4_profit_candidates(loader):
    """Test genuine candidate execution for Net Operating Profit Prediction."""
    # LightGBM (Winner)
    req_lgb = ProfitPredictionRequest(model_type="lightgbm", projected_revenue=500000.0)
    res_lgb = predict_profit(req_lgb, loader)
    assert isinstance(res_lgb.predicted_profit, float)
    assert "LightGBM" in res_lgb.model_name

    # Random Forest
    req_rf = ProfitPredictionRequest(model_type="random_forest", projected_revenue=500000.0)
    res_rf = predict_profit(req_rf, loader)
    assert "Random Forest" in res_rf.model_name

    # Margin Bridge
    req_mb = ProfitPredictionRequest(model_type="margin_bridge", projected_revenue=500000.0)
    res_mb = predict_profit(req_mb, loader)
    assert "Margin Bridge" in res_mb.model_name


# ── 6. Pipeline 5: Expense Prediction ──────────────────────────────────────

def test_pipeline5_expense_candidates(loader):
    """Test genuine candidate execution for Operating Expense Forecasting."""
    # Random Forest (Winner)
    req_rf = ExpensePredictionRequest(category="Salaries", model_type="random_forest")
    res_rf = predict_expense(req_rf, loader)
    assert res_rf.predicted_expense > 0
    assert "Random Forest" in res_rf.model_name

    # XGBoost
    req_xgb = ExpensePredictionRequest(category="Salaries", model_type="xgboost")
    res_xgb = predict_expense(req_xgb, loader)
    assert "XGBoost" in res_xgb.model_name

    # Linear Regression
    req_lr = ExpensePredictionRequest(category="Salaries", model_type="linear_regression")
    res_lr = predict_expense(req_lr, loader)
    assert "Linear Regression" in res_lr.model_name


# ── 7. Pipeline 6: Business Health Score ────────────────────────────────────

def test_pipeline6_business_health_scorecard(loader):
    """Test Business Health Scorecard calculation and forward transition."""
    req = BusinessHealthRequest(
        revenue_growth=0.25,
        profit_margin=0.20,
        expense_control=0.85,
        inventory_turnover=6.0,
        payment_collection=0.92,
    )
    res = calculate_business_health(req, loader)
    assert 0.0 <= res.health_score <= 100.0
    assert res.health_grade in ["A", "B", "C", "D", "F"]
    assert len(res.sub_scores) == 5
    assert len(res.recommendations) > 0
    assert res.projected_next_month_health_score is not None


# ── 8. Pipeline 7: Anomaly Detection ───────────────────────────────────────

def test_pipeline7_anomaly_candidates(loader):
    """Test genuine candidate execution for Anomaly Detection."""
    # Normal transaction with Rule-Based (Winner)
    req_normal = AnomalyDetectionRequest(net_amount=15000.0, discount_pct=5.0, model_type="rule_based")
    res_normal = detect_anomaly(req_normal, loader)
    assert res_normal.is_anomaly is False
    assert res_normal.severity == "NORMAL"

    # Extreme anomalous transaction with Rule-Based
    req_anomaly = AnomalyDetectionRequest(net_amount=120000.0, discount_pct=45.0, model_type="rule_based")
    res_anomaly = detect_anomaly(req_anomaly, loader)
    assert res_anomaly.is_anomaly is True
    assert res_anomaly.severity in ["HIGH", "CRITICAL"]

    # Isolation Forest
    req_if = AnomalyDetectionRequest(net_amount=120000.0, discount_pct=45.0, model_type="isolation_forest")
    res_if = detect_anomaly(req_if, loader)
    assert "Isolation Forest" in res_if.model_name

    # Robust MAD
    req_mad = AnomalyDetectionRequest(net_amount=120000.0, discount_pct=45.0, model_type="robust_mad")
    res_mad = detect_anomaly(req_mad, loader)
    assert "Robust MAD" in res_mad.model_name


# ── 9. Validation & Schema Boundary Tests ──────────────────────────────────

def test_input_validation_boundaries():
    """Verify that pydantic schemas reject invalid boundary inputs."""
    with pytest.raises(Exception):
        # Months ahead must be >= 1 and <= 24
        RevenuePredictionRequest(months_ahead=0)

    with pytest.raises(Exception):
        RevenuePredictionRequest(months_ahead=30)

    with pytest.raises(Exception):
        # Discount must be <= 100
        AnomalyDetectionRequest(net_amount=1000.0, discount_pct=150.0)


# ── 10. HTTP Endpoint Integration & Auth / Tenant Isolation ────────────────

from unittest.mock import MagicMock
from uuid import UUID
from app.dependencies.auth import get_request_context
from app.services.context import RequestContext

TEST_COMPANY_A = UUID("11111111-1111-1111-1111-111111111111")
TEST_COMPANY_B = UUID("22222222-2222-2222-2222-222222222222")
TEST_USER_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def test_unauthenticated_request_rejected():
    """Verify unauthenticated requests return 401."""
    client = TestClient(app)
    # Ensure no override is active
    app.dependency_overrides.pop(get_request_context, None)
    res = client.get("/api/v1/ml/models/registry")
    assert res.status_code == 401


def test_http_model_registry_endpoint():
    """Verify GET /api/v1/ml/models/registry returns 200 with canonical registry."""
    client = TestClient(app)
    mock_supabase = MagicMock()
    ctx = RequestContext(
        user_id=TEST_USER_A,
        company_id=TEST_COMPANY_A,
        user_client=mock_supabase,
        role_id=None,
        permissions=["ml:read", "ml:write"],
    )
    app.dependency_overrides[get_request_context] = lambda: ctx
    try:
        res = client.get("/api/v1/ml/models/registry")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        reg = body["data"]
        assert "revenue_forecasting" in reg
        assert "sales_forecasting" in reg
        assert "inventory_prediction" in reg
        assert "profit_prediction" in reg
        assert "expense_prediction" in reg
        assert "business_health_score" in reg
        assert "anomaly_detection" in reg
    finally:
        app.dependency_overrides.pop(get_request_context, None)


def test_tenant_isolation_in_prediction_logging():
    """Verify that predictions are logged under the authenticated tenant's company_id."""
    client = TestClient(app)
    mock_supabase = MagicMock()
    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.is_.return_value = mock_query
    mock_query.neq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.execute.return_value = MagicMock(data=[])
    mock_supabase.table.return_value = mock_query

    ctx = RequestContext(
        user_id=TEST_USER_A,
        company_id=TEST_COMPANY_A,
        user_client=mock_supabase,
        role_id=None,
        permissions=["ml:read", "ml:write"],
    )
    app.dependency_overrides[get_request_context] = lambda: ctx
    try:
        res = client.post(
            "/api/v1/ml/revenue/predict",
            json={"months_ahead": 3, "model_type": "aagf"}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["model_name"] is not None
        assert body["data"]["data_provenance"] is not None

        # Verify that insert to 'predictions' was called with company_id == TEST_COMPANY_A
        mock_supabase.table.assert_any_call("predictions")
        insert_calls = [
            call for call in mock_query.insert.call_args_list
        ]
        assert len(insert_calls) > 0
        inserted_record = insert_calls[0][0][0]
        assert str(inserted_record["company_id"]) == str(TEST_COMPANY_A)
        assert inserted_record["company_id"] != str(TEST_COMPANY_B)
    finally:
        app.dependency_overrides.pop(get_request_context, None)

