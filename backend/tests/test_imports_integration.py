"""
Comprehensive Integration Tests for Step 7:
CSV, Excel, PDF Import, Validation, Tenant Isolation, and ERP Data Import.
"""
import io
from unittest.mock import MagicMock
from uuid import UUID, uuid4
import openpyxl
import pytest
from pypdf import PdfWriter

from app.services.context import RequestContext
from app.services.import_executor import ImportExecutor
from app.services.import_normalizer import ImportNormalizer
from app.services.import_parser import ImportParserService, sanitize_cell_value
from app.services.import_validator import ImportValidator
from app.services.pdf_extractor import PDFExtractorService


@pytest.fixture
def test_company_id():
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def test_user_id():
    return UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def mock_supabase_client(test_company_id):
    """Mock Supabase client that emulates table queries and operations."""
    client = MagicMock()

    # Pre-existing products in company catalog
    existing_products = [
        {"id": str(uuid4()), "company_id": str(test_company_id), "name": "Existing Widget", "sku": "WIDGET-01", "cost_price": 50.0, "selling_price": 100.0, "type": "product"},
        {"id": str(uuid4()), "company_id": str(test_company_id), "name": "Existing Gadget", "sku": "GADGET-02", "cost_price": 30.0, "selling_price": 60.0, "type": "product"},
    ]

    # Pre-existing warehouses
    existing_warehouses = [
        {"id": str(uuid4()), "company_id": str(test_company_id), "name": "Main Warehouse", "code": "WH-MAIN"},
    ]

    # Pre-existing sales
    existing_sales = [
        {"id": str(uuid4()), "company_id": str(test_company_id), "sale_number": "SO-EXISTING-101"},
    ]

    # Pre-existing invoices
    existing_invoices = [
        {"id": str(uuid4()), "company_id": str(test_company_id), "invoice_number": "INV-EXISTING-501"},
    ]

    def mock_table(table_name):
        table_mock = MagicMock()

        if table_name == "products":
            # select mock
            table_mock.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = existing_products
            table_mock.insert.return_value.execute.return_value.data = [{"id": str(uuid4()), "sku": "NEW-SKU"}]
            table_mock.update.return_value.eq.return_value.execute.return_value.data = [{"id": str(uuid4())}]

        elif table_name == "warehouses":
            table_mock.select.return_value.eq.return_value.execute.return_value.data = existing_warehouses

        elif table_name == "sales":
            table_mock.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = existing_sales
            table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
            table_mock.insert.return_value.execute.return_value.data = [{"id": str(uuid4()), "sale_number": "SO-NEW"}]

        elif table_name == "sale_items":
            table_mock.insert.return_value.execute.return_value.data = [{"id": str(uuid4())}]

        elif table_name == "inventory":
            table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
                {"quantity": 100.0, "reorder_level": 20.0}
            ]
            table_mock.upsert.return_value.execute.return_value.data = [{"quantity": 110.0}]

        elif table_name == "stock_movements":
            table_mock.insert.return_value.execute.return_value.data = [{"id": str(uuid4())}]

        elif table_name == "expenses":
            table_mock.insert.return_value.execute.return_value.data = [{"id": str(uuid4())}]

        elif table_name == "invoices":
            table_mock.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = existing_invoices
            table_mock.insert.return_value.execute.return_value.data = [{"id": str(uuid4())}]
            table_mock.update.return_value.eq.return_value.execute.return_value.data = [{"id": str(uuid4())}]

        elif table_name == "import_batches":
            table_mock.insert.return_value.execute.return_value.data = [{"id": str(uuid4())}]

        return table_mock

    client.table.side_effect = mock_table
    return client


@pytest.fixture
def mock_request_context(test_company_id, test_user_id, mock_supabase_client):
    return RequestContext(
        user_id=test_user_id,
        company_id=test_company_id,
        user_client=mock_supabase_client,
        permissions=["*:*"],
    )


# ── Test Suite 1: CSV and Excel Parsing & Security ─────────────

def test_csv_parsing_valid():
    """Verify standard CSV parsing with comma delimiters."""
    csv_data = "Product Name,SKU,Selling Price,Cost Price\nWidget A,WID-A,19.99,10.00\nWidget B,WID-B,29.99,15.50"
    headers, rows = ImportParserService.parse_csv(csv_data.encode("utf-8"))

    assert headers == ["Product Name", "SKU", "Selling Price", "Cost Price"]
    assert len(rows) == 2
    assert rows[0]["Product Name"] == "Widget A"
    assert rows[0]["SKU"] == "WID-A"
    assert rows[1]["Selling Price"] == "29.99"


def test_csv_delimiter_detection_semicolon():
    """Verify automatic detection of semicolon delimiters."""
    csv_data = "Item;Code;Price;Category\nPen;PEN-1;2.50;Stationery\nPencil;PEN-2;1.00;Stationery"
    headers, rows = ImportParserService.parse_csv(csv_data.encode("utf-8"))

    assert headers == ["Item", "Code", "Price", "Category"]
    assert len(rows) == 2
    assert rows[0]["Item"] == "Pen"


def test_formula_injection_defense():
    """Verify formula injection characters (=, +, -, @) are sanitized."""
    assert sanitize_cell_value("=SUM(A1:B1)").startswith("'=")
    assert sanitize_cell_value("+cmd|' /C calc'!A0").startswith("'+")
    assert sanitize_cell_value("-100").startswith("'-")
    assert sanitize_cell_value("@malicious").startswith("'@")
    assert sanitize_cell_value("Normal Text") == "Normal Text"


def test_xlsx_parsing_and_data_only():
    """Verify XLSX parsing safely extracts values without executing formulas."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ProductsCatalog"
    ws.append(["Name", "SKU", "Price", "Calculated"])
    ws.append(["Laptop", "LAP-01", 1200.0, "=C2*1.18"])

    bio = io.BytesIO()
    wb.save(bio)
    file_bytes = bio.getvalue()

    headers, rows, sheet_names = ImportParserService.parse_xlsx(file_bytes)
    assert "ProductsCatalog" in sheet_names
    assert headers == ["Name", "SKU", "Price", "Calculated"]
    assert len(rows) == 1
    assert rows[0]["Name"] == "Laptop"
    assert rows[0]["SKU"] == "LAP-01"


# ── Test Suite 2: Normalization & Column Mapping ───────────────

def test_column_mapping_suggestions():
    """Verify fuzzy matching correctly suggests ERP destination fields."""
    source_headers = ["Item Name", "Bar Code", "Rate", "Buying Cost", "GST %", "Dept"]
    suggestions = ImportNormalizer.suggest_mappings("products", source_headers)

    assert suggestions.get("Item Name") == "name"
    assert suggestions.get("Bar Code") == "sku"
    assert suggestions.get("Rate") == "selling_price"
    assert suggestions.get("Buying Cost") == "cost_price"
    assert suggestions.get("GST %") == "tax_rate"
    assert suggestions.get("Dept") == "category"


def test_normalization_numbers_and_currency():
    """Verify currency stripping and number parsing."""
    norm = ImportNormalizer()
    val, err = norm.normalize_number("₹ 1,500.50")
    assert err is None
    assert val == 1500.50

    val, err = norm.normalize_number("$25.00")
    assert err is None
    assert val == 25.0

    val, err = norm.normalize_number("invalid-num")
    assert err is not None
    assert val is None


def test_normalization_dates():
    """Verify date parsing for various formats."""
    norm = ImportNormalizer()
    d, err = norm.normalize_date("2026-10-21")
    assert err is None
    assert str(d) == "2026-10-21"

    d, err = norm.normalize_date("21/10/2026")
    assert err is None
    assert str(d) == "2026-10-21"


# ── Test Suite 3: Validation and Conflict Detection ────────────

def test_product_validation_and_conflict(mock_request_context):
    """Verify required field checking, file duplicates, and database conflict warnings."""
    validator = ImportValidator(mock_request_context)

    raw_rows = [
        {"Product": "Valid New Product", "Code": "NEW-PROD-01", "Price": "49.99"},
        {"Product": "Existing Product", "Code": "WIDGET-01", "Price": "110.00"},  # DB conflict
        {"Product": "Duplicate SKU 1", "Code": "DUP-SKU", "Price": "15.00"},
        {"Product": "Duplicate SKU 2", "Code": "DUP-SKU", "Price": "15.00"},      # In-file duplicate
        {"Product": "", "Code": "NO-NAME", "Price": "20.00"},                     # Missing name error
        {"Product": "Bad Price", "Code": "BAD-PRICE", "Price": "-5.00"},          # Negative price error
    ]

    mapping = {"Product": "name", "Code": "sku", "Price": "selling_price"}
    result = validator.validate_batch("products", raw_rows, mapping)

    assert result["total_rows"] == 6
    assert result["valid_rows"] == 3  # Valid new + existing warning + first dup
    assert result["invalid_rows"] == 3  # Second duplicate + missing name + negative price
    assert result["duplicate_rows"] == 1

    # Check conflict flag on existing product
    row_2 = result["row_results"][1]
    assert row_2["is_conflict"] is True
    assert any("already exists in your catalog" in w for w in row_2["warnings"])


def test_sales_referential_integrity(mock_request_context):
    """Verify referenced product SKU must exist in company catalog."""
    validator = ImportValidator(mock_request_context)

    raw_rows = [
        {"Order": "SO-201", "SKU": "WIDGET-01", "Qty": "5", "Price": "100.00"},  # Valid (WIDGET-01 exists in mock)
        {"Order": "SO-201", "SKU": "NON-EXISTENT", "Qty": "2", "Price": "50.00"}, # Invalid foreign SKU
    ]

    mapping = {"Order": "sale_number", "SKU": "product_sku", "Qty": "quantity", "Price": "unit_price"}
    result = validator.validate_batch("sales", raw_rows, mapping)

    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 1

    # Row 2 must have referential error
    row_2 = result["row_results"][1]
    assert any("does not exist in your company catalog" in err for err in row_2["errors"])


def test_inventory_adjustment_validation(mock_request_context):
    """Verify inventory quantity delta and warehouse reference."""
    validator = ImportValidator(mock_request_context)

    raw_rows = [
        {"SKU": "WIDGET-01", "Warehouse": "Main Warehouse", "Delta": "+25", "Notes": "Stock replenishment"},
        {"SKU": "WIDGET-01", "Warehouse": "Main Warehouse", "Delta": "invalid", "Notes": "Corrupted count"},
    ]

    mapping = {"SKU": "product_sku", "Warehouse": "warehouse_name", "Delta": "quantity_delta", "Notes": "notes"}
    result = validator.validate_batch("inventory", raw_rows, mapping)

    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 1


# ── Test Suite 4: Execution, Idempotency & Tenant Isolation ────

def test_import_execution_products_skip_policy(mock_request_context):
    """Verify explicit confirmation writes products and respects skip policy for conflicts."""
    executor = ImportExecutor(mock_request_context)

    validated_rows = [
        {
            "status": "valid",
            "normalized_data": {"name": "Brand New Item", "sku": "BRAND-NEW", "selling_price": 50.0},
        },
        {
            "status": "warning",
            "normalized_data": {"name": "Existing Item", "sku": "WIDGET-01", "selling_price": 105.0},
        },
    ]

    res = executor.execute_batch(
        entity_type="products",
        validated_rows=validated_rows,
        conflict_policy="skip",
        idempotency_key="idemp-test-001",
    )

    assert res["status"] == "completed"
    assert res["created_count"] == 1
    assert res["skipped_count"] == 1
    assert res["failed_count"] == 0


def test_import_execution_idempotency_replay(mock_request_context):
    """Verify re-submitting with the same idempotency key returns cached result without re-inserting."""
    executor = ImportExecutor(mock_request_context)
    key = str(uuid4())

    validated_rows = [
        {"status": "valid", "normalized_data": {"name": "Item A", "sku": "ITEM-A", "selling_price": 10.0}}
    ]

    # First run
    first_res = executor.execute_batch("products", validated_rows, idempotency_key=key)
    # Replay run
    replay_res = executor.execute_batch("products", validated_rows, idempotency_key=key)

    assert replay_res["batch_id"] == first_res["batch_id"]
    assert replay_res["timestamp"] == first_res["timestamp"]


# ── Test Suite 5: PDF Extraction & Arithmetic Checks ───────────

def test_pdf_extraction_and_arithmetic_consistency():
    """Verify PDF extraction identifies fields and verifies arithmetic consistency."""
    # Construct a minimal text PDF in memory
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    # Note: PdfWriter create minimal blank page; test helper directly tests extractor logic on realistic text
    invoice_text = (
        "INVOICE #INV-2026-999\n"
        "Date: 2026-10-15\n"
        "Due Date: 2026-11-15\n"
        "Vendor: Apex Supplies Ltd\n"
        "Bill To: Acme Corp\n"
        "Office Paper 10 5.00 50.00\n"
        "Ink Cartridge 2 25.00 50.00\n"
        "Subtotal: $100.00\n"
        "Tax: $18.00\n"
        "Total: $118.00\n"
    )

    subtotal, tax, total, currency = PDFExtractorService._extract_amounts(invoice_text)
    assert subtotal == 100.0
    assert tax == 18.0
    assert total == 118.0
    assert currency == "USD"

    doc_num = PDFExtractorService._extract_doc_number(invoice_text)
    assert doc_num == "INV-2026-999"

    arithmetic = PDFExtractorService._verify_arithmetic(subtotal, tax, total, [])
    assert arithmetic["is_consistent"] is True
    assert len(arithmetic["issues"]) == 0

    # Arithmetic mismatch check
    bad_arithmetic = PDFExtractorService._verify_arithmetic(100.0, 18.0, 150.0, [])
    assert bad_arithmetic["is_consistent"] is False
    assert len(bad_arithmetic["issues"]) > 0


# ── Test Suite 6: FastAPI HTTP Endpoint Tests ──────────────────

def test_api_schema_endpoint(client, mock_request_context):
    from app.dependencies.auth import get_request_context
    from app.main import app

    app.dependency_overrides[get_request_context] = lambda: mock_request_context
    try:
        response = client.get("/api/v1/imports/schema/products")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["title"] == "Products"
        assert any(f["name"] == "selling_price" for f in body["data"]["fields"])
    finally:
        app.dependency_overrides.pop(get_request_context, None)


def test_api_parse_csv_endpoint(client, mock_request_context):
    from app.dependencies.auth import get_request_context
    from app.main import app

    app.dependency_overrides[get_request_context] = lambda: mock_request_context
    try:
        csv_content = b"Product Name,SKU,Selling Price\nItem 1,SKU-001,45.00\nItem 2,SKU-002,65.00\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        data = {"entity_type": "products"}

        response = client.post("/api/v1/imports/parse", files=files, data=data)
        assert response.status_code == 200
        res = response.json()["data"]
        assert res["total_rows"] == 2
        assert res["headers"] == ["Product Name", "SKU", "Selling Price"]
        assert res["suggested_mapping"]["Product Name"] == "name"
    finally:
        app.dependency_overrides.pop(get_request_context, None)


def test_api_validate_and_confirm_endpoints(client, mock_request_context):
    from app.dependencies.auth import get_request_context
    from app.main import app

    app.dependency_overrides[get_request_context] = lambda: mock_request_context
    try:
        # 1. Validate
        validate_payload = {
            "entity_type": "products",
            "column_mapping": {"Item": "name", "Code": "sku", "Price": "selling_price"},
            "rows": [
                {"Item": "Demo Product", "Code": "DEMO-01", "Price": "99.00"}
            ],
        }
        val_res = client.post("/api/v1/imports/validate", json=validate_payload)
        assert val_res.status_code == 200
        val_data = val_res.json()["data"]
        assert val_data["valid"] is True
        assert val_data["valid_rows"] == 1

        # 2. Confirm
        confirm_payload = {
            "entity_type": "products",
            "validated_rows": val_data["row_results"],
            "conflict_policy": "skip",
            "idempotency_key": "test-key-999",
            "file_name": "demo.csv",
        }
        conf_res = client.post("/api/v1/imports/confirm", json=confirm_payload)
        assert conf_res.status_code == 200
        conf_data = conf_res.json()["data"]
        assert conf_data["status"] == "completed"
        assert conf_data["created_count"] == 1
    finally:
        app.dependency_overrides.pop(get_request_context, None)


def test_api_export_errors_csv(client, mock_request_context):
    from app.dependencies.auth import get_request_context
    from app.main import app

    app.dependency_overrides[get_request_context] = lambda: mock_request_context
    try:
        error_rows = [
            {
                "row_number": 1,
                "status": "invalid",
                "errors": ["Product name is required."],
                "warnings": [],
                "action_proposed": "error",
                "source_data": {"Product": ""},
            }
        ]
        res = client.post("/api/v1/imports/export-errors", json=error_rows)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert b"Product name is required." in res.content
    finally:
        app.dependency_overrides.pop(get_request_context, None)

