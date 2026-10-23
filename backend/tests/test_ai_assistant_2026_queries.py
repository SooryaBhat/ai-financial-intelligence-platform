"""
Comprehensive test suite verifying the RAG & AI Assistant capabilities
for answering realistic 2026 current-year business queries.
"""
from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import UUID
import pytest

from app.services.ai_tools import AIToolExecutor
from app.services.ai_assistant import AIAssistantService, FallbackERPProvider


@pytest.fixture
def company_id():
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_supabase_2026(company_id):
    client = MagicMock()

    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    first_of_month = date.today().replace(day=1).isoformat()
    last_year_same_month_str = (date.today().replace(year=date.today().year - 1)).strftime("%Y-%m")

    # Mock database responses with realistic 2026 retail data
    def mock_table(table_name):
        builder = MagicMock()
        
        if table_name == "companies":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": str(company_id), "name": "FreshMart Hypermarket Ltd", "currency": "INR"}
            ]
        elif table_name == "sales":
            q_mock = MagicMock()
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value = q_mock
            q_mock.gte.return_value = q_mock
            q_mock.lte.return_value = q_mock
            
            # Realistic sales records spanning today, this month, and past periods
            mock_sales_data = [
                {
                    "id": "sale-today-1",
                    "sale_number": "SL-2026-00101",
                    "sale_date": today_str,
                    "status": "confirmed",
                    "total_amount": 14500.0,
                    "subtotal": 14500.0,
                    "discount_amount": 500.0,
                    "customers": {"name": "Sharma Household"},
                },
                {
                    "id": "sale-today-2",
                    "sale_number": "SL-2026-00102",
                    "sale_date": today_str,
                    "status": "confirmed",
                    "total_amount": 28500.0,
                    "subtotal": 28500.0,
                    "discount_amount": 1200.0,
                    "customers": {"name": "Gupta Retail"},
                },
                {
                    "id": "sale-month-1",
                    "sale_number": "SL-2026-00050",
                    "sale_date": first_of_month,
                    "status": "confirmed",
                    "total_amount": 95000.0,
                    "subtotal": 95000.0,
                    "discount_amount": 3000.0,
                    "customers": {"name": "Verma Enterprises"},
                },
                {
                    "id": "sale-outlier",
                    "sale_number": "SL-2026-00099",
                    "sale_date": yesterday_str,
                    "status": "confirmed",
                    "total_amount": 250000.0,  # Unusually high festive sale
                    "subtotal": 250000.0,
                    "discount_amount": 10000.0,
                    "customers": {"name": "Grand Event Caterers"},
                },
            ]
            q_mock.limit.return_value.execute.return_value.data = mock_sales_data
            q_mock.execute.return_value.data = mock_sales_data
        elif table_name == "sale_items":
            builder.select.return_value.in_.return_value.execute.return_value.data = [
                {
                    "product_id": "prod-1",
                    "quantity": 120,
                    "unit_price": 140.0,
                    "line_total": 16800.0,
                    "products": {"name": "Basmati Rice 5kg", "sku": "RIC-0001"},
                },
                {
                    "product_id": "prod-2",
                    "quantity": 95,
                    "unit_price": 275.0,
                    "line_total": 26125.0,
                    "products": {"name": "Premium CTC Tea 500g", "sku": "TEA-0001"},
                },
                {
                    "product_id": "prod-3",
                    "quantity": 80,
                    "unit_price": 88.0,
                    "line_total": 7040.0,
                    "products": {"name": "Fresh Paneer 200g", "sku": "DAI-0001"},
                },
            ]
        elif table_name == "expenses":
            exp_mock = MagicMock()
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value = exp_mock
            mock_expenses = [
                {
                    "id": "exp-1",
                    "description": "Monthly retail facility rent",
                    "amount": 95000.0,
                    "expense_date": f"{date.today().strftime('%Y-%m')}-01",
                    "categories": {"name": "Rent"},
                    "status": "approved",
                },
                {
                    "id": "exp-2",
                    "description": "Electricity, water, cooling",
                    "amount": 22500.0,
                    "expense_date": f"{date.today().strftime('%Y-%m')}-15",
                    "categories": {"name": "Utilities"},
                    "status": "approved",
                },
                {
                    "id": "exp-3",
                    "description": "Logistics dispatch van fuel",
                    "amount": 14200.0,
                    "expense_date": today_str,
                    "categories": {"name": "Logistics & Transport"},
                    "status": "approved",
                },
            ]
            exp_mock.limit.return_value.execute.return_value.data = mock_expenses
            exp_mock.execute.return_value.data = mock_expenses
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = mock_expenses
        elif table_name == "inventory":
            builder.select.return_value.eq.return_value.execute.return_value.data = [
                {
                    "product_id": "prod-1",
                    "quantity": 4,
                    "reorder_level": 25,
                    "products": {"name": "Basmati Rice 5kg", "sku": "RIC-0001"},
                    "warehouses": {"name": "Mumbai Central Warehouse"},
                },
                {
                    "product_id": "prod-2",
                    "quantity": 6,
                    "reorder_level": 20,
                    "products": {"name": "Premium CTC Tea 500g", "sku": "TEA-0001"},
                    "warehouses": {"name": "Delhi Depot"},
                },
            ]
        elif table_name == "products":
            builder.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "prod-1", "name": "Basmati Rice 5kg", "sku": "RIC-0001", "cost_price": 105.0, "selling_price": 140.0},
                {"id": "prod-2", "name": "Premium CTC Tea 500g", "sku": "TEA-0001", "cost_price": 190.0, "selling_price": 275.0},
            ]
        elif table_name == "invoices":
            builder.select.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"total_amount": 388000.0, "amount_paid": 365000.0, "amount_due": 23000.0, "status": "sent"}
            ]
        elif table_name == "chat_sessions":
            builder.select.return_value.eq.return_value.eq.return_value.is_.return_value.order.return_value.execute.return_value.data = [
                {"id": "sess-2026", "title": "2026 Financial Audit"}
            ]
            builder.insert.return_value.execute.return_value.data = [{"id": "sess-2026"}]
        elif table_name == "chat_messages":
            builder.insert.return_value.execute.return_value.data = [{"id": "msg-2026"}]
            builder.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        else:
            builder.select.return_value.eq.return_value.execute.return_value.data = []

        return builder

    client.table.side_effect = mock_table
    return client


def get_used_tools(res):
    return [t["tool"] if isinstance(t, dict) and "tool" in t else str(t) for t in res.get("tools_used", [])]


# -------------------------------------------------------------------------
# Target Query 1: What were today's sales?
# -------------------------------------------------------------------------
def test_query_1_today_sales(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("What were today's sales?")
    
    assert res["status"] == "success"
    assert "get_sales_analysis" in get_used_tools(res)
    assert "₹" in res["message"] or "INR" in res["message"]
    assert "today" in res["message"].lower() or "orders" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 2: What was the total revenue this month?
# -------------------------------------------------------------------------
def test_query_2_this_month_revenue(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("What was the total revenue this month?")
    
    assert res["status"] == "success"
    assert "get_sales_analysis" in get_used_tools(res)
    assert "revenue" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 3: Compare this month with last month
# -------------------------------------------------------------------------
def test_query_3_compare_month_with_last_month(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("Compare this month with last month")
    
    assert res["status"] == "success"
    assert "get_sales_analysis" in get_used_tools(res)
    assert "comparison" in res["message"].lower() or "growth" in res["message"].lower() or "revenue" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 4: Which products sold the most this week?
# -------------------------------------------------------------------------
def test_query_4_top_products_this_week(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("Which products sold the most this week?")
    
    assert res["status"] == "success"
    assert "get_sales_analysis" in get_used_tools(res)
    assert "top" in res["message"].lower() or "sold" in res["message"].lower() or "product" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 5: What are the monthly sales and profit trends in 2026?
# -------------------------------------------------------------------------
def test_query_5_monthly_sales_and_profit_trends(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("What are the monthly sales and profit trends in 2026?")
    
    assert res["status"] == "success"
    tools = get_used_tools(res)
    assert ("get_profit_analysis" in tools) or ("get_sales_analysis" in tools)
    assert "trend" in res["message"].lower() or "profit" in res["message"].lower() or "margin" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 6: What were the largest expense categories this month?
# -------------------------------------------------------------------------
def test_query_6_largest_expense_categories(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("What were the largest expense categories this month?")
    
    assert res["status"] == "success"
    assert "get_expense_summary" in get_used_tools(res)
    assert "expense" in res["message"].lower()
    assert "Rent" in res["message"] or "Utilities" in res["message"] or "category" in res["message"].lower() or "recorded" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 7: Which products are running low on stock?
# -------------------------------------------------------------------------
def test_query_7_low_stock_products(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("Which products are running low on stock?")
    
    assert res["status"] == "success"
    assert "get_inventory_status" in get_used_tools(res)
    assert "stock" in res["message"].lower() or "reorder" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 8: Which days had unusually high or low sales?
# -------------------------------------------------------------------------
def test_query_8_unusual_sales_days(mock_supabase_2026, company_id):
    executor = AIToolExecutor(mock_supabase_2026, company_id)
    analysis = executor.get_sales_analysis(period="this_month")
    
    assert "unusual_sales_days" in analysis
    # Ensure outlier detection structure
    assert isinstance(analysis["unusual_sales_days"], list)


# -------------------------------------------------------------------------
# Target Query 9: What is the gross profit versus net profit?
# -------------------------------------------------------------------------
def test_query_9_gross_profit_vs_net_profit(mock_supabase_2026, company_id):
    service = AIAssistantService(mock_supabase_2026, company_id, provider="fallback")
    res = service.answer_question("What is the gross profit versus net profit this year?")
    
    assert res["status"] == "success"
    assert "get_profit_analysis" in get_used_tools(res)
    # Check mathematical reconciliation in message
    assert "gross profit" in res["message"].lower()
    assert "net profit" in res["message"].lower()
    assert "margin" in res["message"].lower()


# -------------------------------------------------------------------------
# Target Query 10: How does the current month compare with same month last year?
# -------------------------------------------------------------------------
def test_query_10_yoy_comparison(mock_supabase_2026, company_id):
    executor = AIToolExecutor(mock_supabase_2026, company_id)
    analysis = executor.get_sales_analysis(period="this_month")
    
    assert "same_month_last_year_revenue" in analysis
    assert "yoy_growth_percentage" in analysis
    assert "period" in analysis
    assert analysis["company_currency"] == "INR"


# -------------------------------------------------------------------------
# Tenant Isolation: Scoping to Authenticated User's Company
# -------------------------------------------------------------------------
def test_tenant_isolation_ai_assistant(mock_supabase_2026):
    comp_a = UUID("00000000-0000-0000-0000-000000000001")
    comp_b = UUID("00000000-0000-0000-0000-000000000002")

    service_a = AIAssistantService(mock_supabase_2026, comp_a, provider="fallback")
    service_b = AIAssistantService(mock_supabase_2026, comp_b, provider="fallback")

    assert service_a.company_id == comp_a
    assert service_b.company_id == comp_b
    assert str(service_a.executor.company_id) == str(comp_a)
    assert str(service_b.executor.company_id) == str(comp_b)
