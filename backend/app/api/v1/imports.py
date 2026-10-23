"""
Imports API Router — /api/v1/imports
Supports parsing, column mapping, multi-layer validation, explicit confirmation,
idempotency, error reporting, and PDF document extraction.
"""
import csv
import io
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.dependencies.auth import get_request_context
from app.exceptions import ValidationError
from app.schemas.common import SuccessResponse
from app.services.context import RequestContext
from app.services.import_executor import _BATCH_CACHE, ImportExecutor
from app.services.import_normalizer import ENTITY_SCHEMAS, ImportNormalizer
from app.services.import_parser import ImportParserService
from app.services.import_validator import ImportValidator
from app.services.pdf_extractor import PDFExtractorService

router = APIRouter(prefix="/imports", tags=["Data Import"])


# ── Request / Response Schemas ─────────────────────────────────

class ValidateBatchRequest(BaseModel):
    entity_type: str = Field(..., description="Target entity type: products, sales, inventory, expenses, invoices")
    column_mapping: Dict[str, str] = Field(..., description="Mapping of source_header -> dest_field")
    rows: List[Dict[str, Any]] = Field(..., description="Raw parsed data rows")


class ConfirmBatchRequest(BaseModel):
    entity_type: str
    validated_rows: List[Dict[str, Any]]
    conflict_policy: str = Field(default="skip", description="'skip' to ignore existing records or 'update' to update")
    idempotency_key: Optional[str] = None
    file_name: Optional[str] = "uploaded_file"
    source_format: Optional[str] = "csv"


class CreatePdfRecordRequest(BaseModel):
    record_type: str = Field(..., description="'invoice' or 'expense'")
    data: Dict[str, Any] = Field(..., description="User-verified fields from PDF")


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/schema/{entity_type}", response_model=SuccessResponse, summary="Get entity import schema")
def get_import_schema(
    entity_type: str,
    ctx: RequestContext = Depends(get_request_context),
):
    try:
        schema = ImportNormalizer.get_entity_schema(entity_type)
        return SuccessResponse(data=schema)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/parse", response_model=SuccessResponse, summary="Upload and parse CSV/XLSX file")
async def parse_file(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Parse uploaded file, extract headers, sample preview rows, and suggest column mappings.
    Does NOT write any business records.
    """
    try:
        file_bytes = await file.read()
        file_ext = ImportParserService.validate_file_metadata(file.filename or "file", file_bytes)

        sheet_names: List[str] = []
        if file_ext == ".csv":
            headers, rows = ImportParserService.parse_csv(file_bytes)
        elif file_ext == ".xlsx":
            headers, rows, sheet_names = ImportParserService.parse_xlsx(file_bytes, sheet_name=sheet_name)
        elif file_ext == ".pdf":
            raise ValidationError("Please use the PDF Document Extraction endpoint for .pdf files.")
        else:
            raise ValidationError(f"Unsupported extension '{file_ext}'")

        # Suggest column mappings
        suggested_mapping = ImportNormalizer.suggest_mappings(entity_type, headers)

        return SuccessResponse(data={
            "file_name": file.filename,
            "source_format": file_ext.replace(".", ""),
            "total_rows": len(rows),
            "headers": headers,
            "sheet_names": sheet_names,
            "selected_sheet": sheet_name or (sheet_names[0] if sheet_names else None),
            "preview_rows": rows[:10],
            "all_rows": rows,  # Provided for client mapping & validation pipeline
            "suggested_mapping": suggested_mapping,
        })
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ve.message)
    except Exception as e:
        logger.error("Error parsing file | filename={} error={}", file.filename, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse file: {str(e)}")


@router.post("/validate", response_model=SuccessResponse, summary="Validate mapped rows without writing")
def validate_batch(
    payload: ValidateBatchRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Validate mapped rows against database and schema rules.
    Identifies valid, warning, duplicate, and invalid rows.
    Does NOT write any records to database.
    """
    try:
        validator = ImportValidator(ctx)
        result = validator.validate_batch(
            entity_type=payload.entity_type,
            raw_rows=payload.rows,
            column_mapping=payload.column_mapping,
        )
        return SuccessResponse(data=result)
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ve.message)
    except Exception as e:
        logger.error("Validation error | company={} error={}", ctx.company_id, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Validation error: {str(e)}")


@router.post("/confirm", response_model=SuccessResponse, summary="Confirm and execute validated import")
def confirm_batch(
    payload: ConfirmBatchRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Execute confirmed import batch into database with idempotency and conflict policy.
    Strictly isolated to ctx.company_id and ctx.branch_id.
    """
    try:
        executor = ImportExecutor(ctx)
        summary = executor.execute_batch(
            entity_type=payload.entity_type,
            validated_rows=payload.validated_rows,
            conflict_policy=payload.conflict_policy,
            idempotency_key=payload.idempotency_key,
            file_name=payload.file_name or "uploaded_file",
            source_format=payload.source_format or "csv",
        )
        return SuccessResponse(data=summary)
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ve.message)
    except Exception as e:
        logger.error("Import confirmation error | company={} error={}", ctx.company_id, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Execution error: {str(e)}")


@router.post("/pdf/extract", response_model=SuccessResponse, summary="Extract candidate fields from PDF document")
async def extract_pdf(
    file: UploadFile = File(...),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Extract candidate text, fields, line items, and verify arithmetic consistency from PDF.
    Does NOT create records without explicit review.
    """
    try:
        file_bytes = await file.read()
        ImportParserService.validate_file_metadata(file.filename or "doc.pdf", file_bytes)

        if not (file.filename or "").lower().endswith(".pdf"):
            raise ValidationError("File must be a PDF document.")

        result = PDFExtractorService.extract_document(file_bytes, file.filename or "document.pdf")
        return SuccessResponse(data=result)
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ve.message)
    except Exception as e:
        logger.error("PDF extraction error | filename={} error={}", file.filename, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"PDF extraction error: {str(e)}")


@router.post("/pdf/create-record", response_model=SuccessResponse, summary="Create ERP record from reviewed PDF data")
def create_record_from_pdf(
    payload: CreatePdfRecordRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Creates an Invoice or Expense record after user review and explicit confirmation.
    """
    try:
        data = payload.data
        if payload.record_type == "invoice":
            inv_payload = {
                "company_id": str(ctx.company_id),
                "invoice_number": data.get("document_number") or f"INV-PDF-{str(UUID.int)[:6]}",
                "invoice_type": data.get("invoice_type") or "receivable",
                "invoice_date": data.get("issue_date") or str(date.today()),
                "due_date": data.get("due_date"),
                "subtotal": float(data.get("subtotal") or data.get("total_amount") or 0.0),
                "tax_amount": float(data.get("tax_amount") or 0.0),
                "total_amount": float(data.get("total_amount") or 0.0),
                "currency": data.get("currency") or "USD",
                "status": "draft",
                "notes": f"Created via verified PDF extraction: {data.get('notes', '')}".strip(),
            }
            res = ctx.user_client.table("invoices").insert(inv_payload).execute()
            return SuccessResponse(data=res.data[0] if res.data else {})

        elif payload.record_type == "expense":
            exp_payload = {
                "company_id": str(ctx.company_id),
                "branch_id": str(ctx.branch_id) if ctx.branch_id else None,
                "created_by": str(ctx.user_id) if ctx.user_id else None,
                "description": data.get("description") or f"Receipt #{data.get('document_number', 'N/A')}",
                "amount": float(data.get("total_amount") or data.get("amount") or 0.0),
                "expense_date": data.get("issue_date") or str(date.today()),
                "payment_method": data.get("payment_method") or "cash",
                "status": "pending",
                "notes": f"Created via verified PDF extraction: {data.get('notes', '')}".strip(),
            }
            res = ctx.user_client.table("expenses").insert(exp_payload).execute()
            return SuccessResponse(data=res.data[0] if res.data else {})

        else:
            raise ValidationError(f"Unsupported record_type '{payload.record_type}'")

    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ve.message)
    except Exception as e:
        logger.error("Error creating record from PDF | company={} error={}", ctx.company_id, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history", response_model=SuccessResponse, summary="List recent import batches")
def list_import_history(
    ctx: RequestContext = Depends(get_request_context),
):
    """
    List recent import batches for active company.
    Queries import_batches table if available, otherwise returns cached items.
    """
    try:
        res = (
            ctx.user_client.table("import_batches")
            .select("*")
            .eq("company_id", str(ctx.company_id))
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        if res.data:
            return SuccessResponse(data=res.data)
    except Exception:
        pass

    # Fallback to in-memory cache filtered by company_id
    comp_str = str(ctx.company_id)
    cached = [b for b in _BATCH_CACHE.values() if b.get("company_id") == comp_str]
    return SuccessResponse(data=cached)


@router.post("/export-errors", summary="Download validation error report as CSV")
def export_error_report(
    row_results: List[Dict[str, Any]],
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Streams CSV report containing all rows that had validation errors or warnings.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Row Number", "Status", "Errors", "Warnings", "Proposed Action", "Raw Source Data"])
    for r in row_results:
        if r.get("status") in ("invalid", "warning"):
            writer.writerow([
                r.get("row_number"),
                r.get("status"),
                "; ".join(r.get("errors", [])),
                "; ".join(r.get("warnings", [])),
                r.get("action_proposed"),
                str(r.get("source_data", {})),
            ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=import_validation_errors.csv"},
    )
