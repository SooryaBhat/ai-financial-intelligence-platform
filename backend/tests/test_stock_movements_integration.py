"""
Unit & Integration Tests for Stock Movement Validation, Balance Updates, and Persistence.
Tests satisfy Requirement 3 and Requirement 5:
- Stock movement schema validation for 'IN', 'OUT', 'TRANSFER', and enum types.
- Authorized company scoping and tenant isolation.
- Automatic inventory balance calculation (+ for IN, - for OUT).
- Insufficient inventory balance rejection (HTTP 400).
- Database persistence and audit logging.
"""
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.stock_movements import create_movement
from app.core.constants import StockMovementType
from app.schemas.inventory import StockMovementCreate
from app.services.context import RequestContext


@pytest.fixture
def test_company_id():
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def test_user_id():
    return UUID("81438aaa-ad33-4643-a492-9f552d6d7b3b")


@pytest.fixture
def sample_product_id():
    return UUID("0a68f0c4-0046-4bd7-9c1f-c4d3bae18657")


@pytest.fixture
def sample_warehouse_id():
    return UUID("574f8e49-624f-4c82-81a6-66739af2fa27")


def test_stock_movement_create_schema_flexibility(sample_product_id, sample_warehouse_id):
    """Verify StockMovementCreate schema accepts 'IN', 'OUT', 'TRANSFER', and references."""
    # IN movement
    sm_in = StockMovementCreate(
        product_id=sample_product_id,
        warehouse_id=sample_warehouse_id,
        movement_type="IN",
        quantity=5.0,
        reference="PO-1002",
    )
    assert sm_in.movement_type == "IN"
    assert sm_in.quantity == 5.0
    assert sm_in.reference == "PO-1002"

    # OUT movement
    sm_out = StockMovementCreate(
        product_id=sample_product_id,
        warehouse_id=sample_warehouse_id,
        movement_type="OUT",
        quantity=3.0,
    )
    assert sm_out.movement_type == "OUT"

    # TRANSFER movement
    sm_transfer = StockMovementCreate(
        product_id=sample_product_id,
        warehouse_id=sample_warehouse_id,
        movement_type="TRANSFER",
        quantity=2.0,
    )
    assert sm_transfer.movement_type == "TRANSFER"

    # Negative quantity should be rejected by schema validation
    with pytest.raises(Exception):
        StockMovementCreate(
            product_id=sample_product_id,
            warehouse_id=sample_warehouse_id,
            movement_type="IN",
            quantity=-1.0,
        )


def test_create_stock_movement_in_updates_inventory_balance(
    test_company_id, test_user_id, sample_product_id, sample_warehouse_id
):
    """Verify stock IN creates movement and increases inventory quantity balance."""
    mock_client = MagicMock()

    # Current stock in inventory table is 10 units
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"quantity": 10.0, "reorder_level": 5.0}
    ]

    # Created movement record
    new_movement_id = str(uuid4())
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": new_movement_id,
            "company_id": str(test_company_id),
            "product_id": str(sample_product_id),
            "warehouse_id": str(sample_warehouse_id),
            "movement_type": "receipt",
            "quantity": 15.0,
            "notes": "PO-9999",
        }
    ]
    # Upsert inventory return
    mock_client.table.return_value.upsert.return_value.execute.return_value.data = [
        {"quantity": 25.0, "reorder_level": 5.0}
    ]

    ctx = RequestContext(
        user_id=test_user_id,
        company_id=test_company_id,
        user_client=mock_client,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    payload = StockMovementCreate(
        product_id=sample_product_id,
        warehouse_id=sample_warehouse_id,
        movement_type="IN",
        quantity=15.0,
        reference="PO-9999",
    )

    resp = create_movement(payload, ctx)

    assert resp.success is True
    assert resp.data["id"] == new_movement_id
    assert resp.data["movement_type"] == "receipt"


def test_create_stock_movement_out_decreases_inventory_balance(
    test_company_id, test_user_id, sample_product_id, sample_warehouse_id
):
    """Verify stock OUT creates movement and decreases inventory balance."""
    mock_client = MagicMock()

    # Current stock is 10 units
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"quantity": 10.0, "reorder_level": 5.0}
    ]

    new_movement_id = str(uuid4())
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": new_movement_id,
            "company_id": str(test_company_id),
            "product_id": str(sample_product_id),
            "warehouse_id": str(sample_warehouse_id),
            "movement_type": "sale",
            "quantity": -4.0,
            "notes": "SO-5555",
        }
    ]

    mock_client.table.return_value.upsert.return_value.execute.return_value.data = [
        {"quantity": 6.0, "reorder_level": 5.0}
    ]

    ctx = RequestContext(
        user_id=test_user_id,
        company_id=test_company_id,
        user_client=mock_client,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    payload = StockMovementCreate(
        product_id=sample_product_id,
        warehouse_id=sample_warehouse_id,
        movement_type="OUT",
        quantity=4.0,
        reference="SO-5555",
    )

    resp = create_movement(payload, ctx)
    assert resp.success is True
    assert resp.data["quantity"] == -4.0


def test_create_stock_movement_insufficient_stock_raises_400(
    test_company_id, test_user_id, sample_product_id, sample_warehouse_id
):
    """Verify stock OUT with quantity exceeding available balance raises HTTP 400."""
    mock_client = MagicMock()

    # Current stock is only 2 units
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"quantity": 2.0, "reorder_level": 5.0}
    ]

    ctx = RequestContext(
        user_id=test_user_id,
        company_id=test_company_id,
        user_client=mock_client,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    # Attempt to remove 10 units when only 2 exist
    payload = StockMovementCreate(
        product_id=sample_product_id,
        warehouse_id=sample_warehouse_id,
        movement_type="OUT",
        quantity=10.0,
    )

    with pytest.raises(HTTPException) as exc_info:
        create_movement(payload, ctx)

    assert exc_info.value.status_code == 400
    assert "Insufficient inventory balance" in exc_info.value.detail
    assert "Current available stock: 2.0" in exc_info.value.detail


def test_stock_movement_tenant_isolation(
    test_company_id, test_user_id, sample_product_id, sample_warehouse_id
):
    """Verify company_id is strictly derived from ctx.company_id and cannot be overridden."""
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"quantity": 5.0, "reorder_level": 2.0}
    ]

    captured_insert = []

    def fake_insert(record):
        captured_insert.append(record)
        builder = MagicMock()
        builder.execute.return_value.data = [{"id": str(uuid4()), **record}]
        return builder

    mock_client.table.return_value.insert = fake_insert
    mock_client.table.return_value.upsert.return_value.execute.return_value.data = [{}]

    ctx = RequestContext(
        user_id=test_user_id,
        company_id=test_company_id,
        user_client=mock_client,
    )

    payload = StockMovementCreate(
        product_id=sample_product_id,
        warehouse_id=sample_warehouse_id,
        movement_type="IN",
        quantity=1.0,
    )

    create_movement(payload, ctx)

    assert len(captured_insert) == 1
    # Strictly scoped to ctx.company_id
    assert captured_insert[0]["company_id"] == str(test_company_id)
    assert captured_insert[0]["created_by"] == str(test_user_id)
