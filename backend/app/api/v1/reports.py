"""Reports router — /api/v1/reports"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_request_context
from app.repositories.reports import ReportRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.reports import ReportCreate, ReportUpdate
from app.services.context import RequestContext

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", response_model=SuccessResponse, summary="List reports")
def list_reports(ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    return SuccessResponse(data=repo.list(ctx.company_id))


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create report")
def create_report(payload: ReportCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    data = {
        "company_id": str(ctx.company_id),
        "user_id": str(ctx.user_id),
        "report_type": payload.report_type.value,
        "title": payload.title,
        "period_start": payload.period_start.isoformat() if payload.period_start else None,
        "period_end": payload.period_end.isoformat() if payload.period_end else None,
        "status": "generating",
    }
    result = repo.create(data)
    return SuccessResponse(data=result)


@router.get("/{report_id}", response_model=SuccessResponse, summary="Get report")
def get_report(report_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(report_id, ctx.company_id))


@router.patch("/{report_id}", response_model=SuccessResponse, summary="Update report")
def update_report(report_id: UUID, payload: ReportUpdate, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    data = repo.update(report_id, payload.model_dump(exclude_none=True), ctx.company_id)
    return SuccessResponse(data=data)


@router.delete("/{report_id}", response_model=MessageResponse, summary="Delete report")
def delete_report(report_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ReportRepository(ctx.user_client)
    repo.soft_delete(report_id, ctx.company_id)
    return MessageResponse(message="Report deleted.")
