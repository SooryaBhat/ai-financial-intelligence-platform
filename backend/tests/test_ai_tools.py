"""
Unit & Integration Tests for AI Assistant Tools (AIToolExecutor).
Tests all 6 enterprise ERP tools with company isolation and data validation.
"""
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from app.services.ai_tools import AIToolExecutor, TOOL_DECLARATIONS


@pytest.fixture
def sample_company_id():
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_supabase_client():
    client = MagicMock()

    def mock_table(table_name):
        builder = MagicMock()

        if table_name == "companies":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": "11111111-1111-1111-1111-111111111111", "currency": "INR", "name": "Apex Manufacturing Ltd"}
            ]
        elif table_name == "sales":
            # Chained calls for sales queries
            query_mock = MagicMock()
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value = query_mock
            query_mock.limit.return_value.execute.return_value.data = [
                {
                    "id": "s-1",
                    "sale_number": "SL-101",
                    "sale_date": "2026-10-01",
                    "status": "confirmed",
                    "total_amount": 150000.0,
                    "subtotal": 150000.0,
                    "discount_amount": 0.0,
                    "customers": {"name": "Reliance Retail"},
                },
                {
                    "id": "s-2",
                    "sale_number": "SL-102",
                    "sale_date": "2026-09-15",
                    "status": "completed",
                    "total_amount": 85000.0,
                    "subtotal": 90000.0,
                    "discount_amount": 5000.0,
                    "customers": {"name": "Tata Consumer"},
                },
            ]
            query_mock.execute.return_value.data = query_mock.limit.return_value.execute.return_value.data
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value.execute.return_value.data = query_mock.limit.return_value.execute.return_value.data
        elif table_name == "sale_items":
            builder.select.return_value.in_.return_value.execute.return_value.data = [
                {
                    "product_id": "p-1",
                    "quantity": 10,
                    "unit_price": 15000.0,
                    "line_total": 150000.0,
                    "products": {"name": "Industrial Sensor A1", "sku": "IND-A1"},
                },
                {
                    "product_id": "p-2",
                    "quantity": 5,
                    "unit_price": 17000.0,
                    "line_total": 85000.0,
                    "products": {"name": "Pressure Valve V2", "sku": "VALVE-V2"},
                },
            ]
        elif table_name == "expenses":
            exp_mock = MagicMock()
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value = exp_mock
            exp_mock.limit.return_value.execute.return_value.data = [
                {
                    "id": "e-1",
                    "description": "Factory Rent",
                    "amount": 45000.0,
                    "expense_date": "2026-10-01",
                    "categories": {"name": "Rent & Facilities"},
                    "status": "approved",
                },
                {
                    "id": "e-2",
                    "description": "Electricity Utility",
                    "amount": 12000.0,
                    "expense_date": "2026-10-05",
                    "categories": {"name": "Utilities"},
                    "status": "approved",
                },
            ]
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value.execute.return_value.data = exp_mock.limit.return_value.execute.return_value.data
        elif table_name == "products":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": "p-1", "name": "Industrial Sensor A1", "sku": "IND-A1"},
                {"id": "p-2", "name": "Pressure Valve V2", "sku": "VALVE-V2"},
                {"id": "p-3", "name": "Conveyor Belt", "sku": "BELT-01"},
            ]
        elif table_name == "inventory":
            builder.select.return_value.eq.return_value.execute.return_value.data = [
                {
                    "product_id": "p-1",
                    "quantity": 4,
                    "reorder_level": 10,
                    "products": {"name": "Industrial Sensor A1", "sku": "IND-A1"},
                    "warehouses": {"name": "Main Depot"},
                },
                {
                    "product_id": "p-2",
                    "quantity": 30,
                    "reorder_level": 15,
                    "products": {"name": "Pressure Valve V2", "sku": "VALVE-V2"},
                    "warehouses": {"name": "Main Depot"},
                },
            ]
        elif table_name == "invoices":
            builder.select.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"total_amount": 100000.0, "amount_paid": 90000.0, "amount_due": 10000.0, "status": "sent"}
            ]
        else:
            builder.select.return_value.eq.return_value.execute.return_value.data = []

        return builder

    client.table.side_effect = mock_table
    return client


def test_tool_declarations_registry():
    """Verify all 8 enterprise tools are declared with schema properties."""
    names = [d["name"] for d in TOOL_DECLARATIONS]
    assert "get_company_profile" in names
    assert "get_sales_analysis" in names
    assert "get_expense_summary" in names
    assert "get_inventory_status" in names
    assert "forecast_revenue" in names
    assert "detect_transaction_anomalies" in names
    assert "get_business_health_analysis" in names
    assert "search_business_knowledge_base" in names
    assert len(TOOL_DECLARATIONS) == 8


def test_tool_sales_analysis(mock_supabase_client, sample_company_id):
    """Test get_sales_analysis returns accurate revenue and product metrics."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)
    result = executor.get_sales_analysis(period="all", limit=5)

    assert result["company_currency"] == "INR"
    assert result["total_revenue"] == 235000.0  # 150000 + 85000
    assert result["total_sales_count"] == 2
    assert result["average_sale_value"] == 117500.0
    assert len(result["top_products"]) == 2
    assert result["top_products"][0]["name"] == "Industrial Sensor A1"
    assert "SL-101" in result["recent_sales"][0]["sale_number"]
    assert "summary" in result


def test_tool_expense_summary(mock_supabase_client, sample_company_id):
    """Test get_expense_summary aggregates category spending."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)
    result = executor.get_expense_summary(period="all", limit=5)

    assert result["company_currency"] == "INR"
    assert result["total_expenses"] == 57000.0  # 45000 + 12000
    assert result["expense_count"] == 2
    assert len(result["category_breakdown"]) == 2
    assert result["category_breakdown"][0]["category"] == "Rent & Facilities"
    assert "summary" in result


def test_tool_inventory_status(mock_supabase_client, sample_company_id):
    """Test get_inventory_status identifies low-stock items correctly."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)
    result = executor.get_inventory_status(low_stock_only=True)

    assert result["total_catalog_products"] == 3
    assert result["total_stock_units"] == 34.0  # 4 + 30
    assert result["low_stock_count"] == 1
    assert result["stock_status"] in ("WARNING", "CRITICAL_STOCKOUT_RISK")
    assert result["low_stock_items"][0]["product_name"] == "Industrial Sensor A1"
    assert result["low_stock_items"][0]["deficit_units"] == 6.0  # 10 - 4


def test_tool_forecast_revenue(mock_supabase_client, sample_company_id):
    """Test forecast_revenue produces valid projections via ML model."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)
    result = executor.forecast_revenue(months_ahead=6, model_type="xgboost")

    assert result["company_currency"] == "INR"
    assert result["forecast_period_months"] == 6
    assert result["total_projected_revenue"] > 0
    assert len(result["predictions"]) == 6
    assert result["growth_trend"] in ("UPWARD", "DOWNWARD", "STABLE")


def test_tool_anomaly_detection(mock_supabase_client, sample_company_id):
    """Test detect_transaction_anomalies runs Isolation Forest on transaction."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)
    
    # Test specific transaction evaluation
    single_res = executor.detect_transaction_anomalies(net_amount=500000.0, discount_pct=65.0)
    assert single_res["is_anomaly"] is True
    assert single_res["severity"] in ("CRITICAL", "HIGH")
    assert "discount" in single_res["reason"].lower() or "deviates" in single_res["reason"].lower()

    # Test batch scan of recent transactions
    batch_res = executor.detect_transaction_anomalies(limit=5)
    assert "scanned_transactions_count" in batch_res
    assert "summary" in batch_res


def test_tool_business_health(mock_supabase_client, sample_company_id):
    """Test get_business_health_analysis calculates composite score."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)
    result = executor.get_business_health_analysis()

    assert 0 <= result["health_score"] <= 100
    assert result["health_grade"] in ("A", "B", "C", "D", "F")
    assert result["risk_rating"] in ("LOW_RISK", "MODERATE_RISK", "HIGH_RISK", "CRITICAL_RISK")
    assert len(result["recommendations"]) > 0
    assert "evaluated_kpis" in result


def test_executor_dispatch_and_unknown_tool(mock_supabase_client, sample_company_id):
    """Test dynamic dispatch through executor.execute."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)

    # Valid dispatch
    res = executor.execute("get_sales_analysis", {"period": "all"})
    assert "total_revenue" in res

    # Unknown tool dispatch
    bad_res = executor.execute("drop_database_table", {})
    assert "error" in bad_res
    assert "not supported" in bad_res["error"]


def test_empty_company_data_handling(sample_company_id):
    """Test graceful handling when company has zero records."""
    empty_client = MagicMock()
    empty_client.table.return_value.select.return_value.eq.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    empty_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    executor = AIToolExecutor(empty_client, sample_company_id)
    sales_res = executor.get_sales_analysis()
    assert sales_res["total_revenue"] == 0.0
    assert sales_res["total_sales_count"] == 0

    exp_res = executor.get_expense_summary()
    assert exp_res["total_expenses"] == 0.0

    inv_res = executor.get_inventory_status()
    assert inv_res["total_catalog_products"] == 0


def test_get_company_profile_tenant_isolation(sample_company_id):
    """Test get_company_profile strictly scopes to self.company_id and returns safe metadata."""
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
        {
            "id": str(sample_company_id),
            "name": "Horizon Retail Ltd",
            "slug": "horizon-retail-ltd",
            "industry": "Retail",
            "country": "India",
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "subscription_status": "trialing",
            "is_active": True,
        }
    ]

    executor = AIToolExecutor(client, sample_company_id)
    profile = executor.get_company_profile()

    assert profile["company_id"] == str(sample_company_id)
    assert profile["company_name"] == "Horizon Retail Ltd"
    assert profile["currency"] == "INR"
    assert profile["industry"] == "Retail"
    assert "Horizon Retail Ltd" in profile["summary"]
    # Verify execute gateway also calls it
    res_gateway = executor.execute("get_company_profile", {})
    assert res_gateway["company_name"] == "Horizon Retail Ltd"


def test_get_sales_analysis_historical_december_2024(mock_supabase_client, sample_company_id):
    """Test get_sales_analysis parses historical period 'december 2024' into ISO range."""
    executor = AIToolExecutor(mock_supabase_client, sample_company_id)
    res = executor.get_sales_analysis(period="december 2024")

    assert res["period"] == "December 2024"
    assert "total_revenue" in res
    assert "December 2024" in res["summary"]


def test_get_sales_analysis_future_empty_period(sample_company_id):
    """Test get_sales_analysis truthfully reports empty period without hallucination."""
    empty_client = MagicMock()
    query_mock = MagicMock()
    empty_client.table.return_value.select.return_value.eq.return_value.is_.return_value.order.return_value = query_mock
    query_mock.gte.return_value = query_mock
    query_mock.lte.return_value = query_mock
    query_mock.limit.return_value.execute.return_value.data = []

    executor = AIToolExecutor(empty_client, sample_company_id)
    res = executor.get_sales_analysis(period="october 2026")

    assert res["total_revenue"] == 0.0
    assert res["total_sales_count"] == 0
    assert "No confirmed sales transactions found" in res["summary"]
    assert "Note: Current recorded historical transactions exist up to December 2024" in res["summary"]

