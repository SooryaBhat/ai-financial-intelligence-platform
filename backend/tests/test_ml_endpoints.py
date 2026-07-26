"""
Pytest integration test suite for ML Prediction REST endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_revenue_predict():
    response = client.post(
        "/api/ml/revenue/predict",
        json={"months_ahead": 6, "model_type": "xgboost"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "predictions" in data["data"]
    assert len(data["data"]["predictions"]) == 6


def test_sales_predict():
    response = client.post(
        "/api/ml/sales/predict",
        json={"entity_type": "product", "model_type": "xgboost", "months_ahead": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["model_used"] is not None


def test_inventory_predict():
    response = client.post(
        "/api/ml/inventory/predict",
        json={"product_name": "Premium Laptop X1", "current_stock": 25.0, "unit_cost": 450.0, "lead_time_days": 14},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "recommended_reorder_point" in data["data"]


def test_profit_predict():
    response = client.post(
        "/api/ml/profit/predict",
        json={"projected_revenue": 22000000.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "predicted_profit" in data["data"]


def test_expense_predict():
    response = client.post(
        "/api/ml/expense/predict",
        json={"category": "Salaries", "model_type": "xgboost"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "predicted_expense" in data["data"]


def test_business_health_predict():
    response = client.post(
        "/api/ml/business-health/predict",
        json={
            "revenue_growth": 0.18,
            "profit_margin": 0.22,
            "expense_control": 0.85,
            "inventory_turnover": 5.2,
            "payment_collection": 0.92,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert 0.0 <= data["data"]["health_score"] <= 100.0


def test_anomaly_predict():
    response = client.post(
        "/api/ml/anomaly/predict",
        json={"net_amount": 125000.0, "discount_pct": 15.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "is_anomaly" in data["data"]
