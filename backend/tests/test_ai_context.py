"""
Tests for AIContextService and Chat API endpoint.
"""
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from app.services.ai_context_service import AIContextService


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client returning sample company & ERP data."""
    client = MagicMock()

    # Mock table query builder chaining
    def mock_table(table_name):
        builder = MagicMock()
        
        if table_name == "companies":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": "00000000-0000-0000-0000-000000000001", "name": "Horizon Retail Ltd", "currency": "INR"}
            ]
        elif table_name == "sales":
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {
                    "id": "s1",
                    "sale_number": "SL-001",
                    "sale_date": "2026-09-15",
                    "status": "confirmed",
                    "total_amount": 125000,
                    "customers": {"name": "Acme Corp"},
                },
                {
                    "id": "s2",
                    "sale_number": "SL-002",
                    "sale_date": "2026-09-20",
                    "status": "delivered",
                    "total_amount": 75000,
                    "customers": {"name": "Beta LLC"},
                },
            ]
        elif table_name == "sale_items":
            builder.select.return_value.in_.return_value.execute.return_value.data = [
                {"quantity": 10, "unit_price": 5000, "line_total": 50000, "product_id": "p1", "products": {"name": "Laptop Stand", "sku": "LS-01"}},
                {"quantity": 5, "unit_price": 15000, "line_total": 75000, "product_id": "p2", "products": {"name": "4K Monitor", "sku": "MON-4K"}},
            ]
        elif table_name == "expenses":
            builder.select.return_value.eq.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {"id": "e1", "description": "Office Rent", "amount": 35000, "expense_date": "2026-09-01", "categories": {"name": "Rent & Utilities"}},
                {"id": "e2", "description": "Internet Subscription", "amount": 5000, "expense_date": "2026-09-05", "categories": {"name": "Rent & Utilities"}},
            ]
        elif table_name == "products":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"id": "p1", "name": "Laptop Stand", "sku": "LS-01"},
                {"id": "p2", "name": "4K Monitor", "sku": "MON-4K"},
            ]
        elif table_name == "inventory":
            builder.select.return_value.eq.return_value.execute.return_value.data = [
                {"product_id": "p1", "quantity": 3, "reorder_level": 10, "products": {"name": "Laptop Stand", "sku": "LS-01"}},
                {"product_id": "p2", "quantity": 25, "reorder_level": 5, "products": {"name": "4K Monitor", "sku": "MON-4K"}},
            ]
        elif table_name == "invoices":
            builder.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
                {"invoice_type": "receivable", "total_amount": 50000, "amount_paid": 20000, "amount_due": 30000, "status": "sent"},
            ]
        else:
            builder.select.return_value.eq.return_value.execute.return_value.data = []

        return builder

    client.table.side_effect = mock_table
    return client


def test_build_business_context(mock_supabase_client):
    company_id = UUID("00000000-0000-0000-0000-000000000001")
    service = AIContextService(mock_supabase_client, company_id)
    
    context = service.build_business_context("What are my top selling products?")
    
    assert "Horizon Retail Ltd" in context
    assert "INR" in context
    assert "Laptop Stand" in context
    assert "4K Monitor" in context
    assert "200,000.00" in context  # Total revenue sum 125000 + 75000
    assert "Rent & Utilities" in context
    assert "Laptop Stand (SKU: LS-01): Current Stock=3.0 units" in context


def test_answer_question_without_api_key(mock_supabase_client):
    company_id = UUID("00000000-0000-0000-0000-000000000001")
    service = AIContextService(mock_supabase_client, company_id)

    with patch("app.services.ai_context_service._get_api_key", return_value=""):
        answer = service.answer_question("How is my business doing?")
        assert "temporarily unavailable" in answer.lower()
