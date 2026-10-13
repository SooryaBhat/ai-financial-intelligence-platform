"""
Companies router — /api/v1/companies
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.companies import CompanyRepository
from app.schemas.common import MessageResponse, PaginatedResponse, SuccessResponse
from app.schemas.companies import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.companies import CompanyService
from app.services.context import RequestContext

router = APIRouter(prefix="/companies", tags=["Companies"])


def _get_service(ctx: RequestContext = Depends(get_request_context)) -> CompanyService:
    return CompanyService(CompanyRepository(ctx.user_client))


@router.get("", response_model=SuccessResponse, summary="List companies")
@router.get("/", response_model=SuccessResponse, summary="List companies", include_in_schema=False)
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    data = svc.list(page=page, page_size=page_size, search=search)
    return SuccessResponse(data=data)


@router.post("", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create company")
@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create company", include_in_schema=False)
def create_company(
    payload: CompanyCreate,
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    data = svc.create(payload, ctx)
    return SuccessResponse(data=data)


@router.get(
    "/me",
    response_model=SuccessResponse,
    summary="Get the current company",
)
def get_current_company(
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    data = svc.get(ctx.company_id, ctx)
    return SuccessResponse(data=data)


@router.patch(
    "/me",
    response_model=SuccessResponse,
    summary="Update the current company",
)
def update_current_company(
    payload: CompanyUpdate,
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    data = svc.update(ctx.company_id, payload, ctx)
    return SuccessResponse(data=data)


@router.get("/{company_id}", response_model=SuccessResponse, summary="Get company by ID")
def get_company_by_id(
    company_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    data = svc.get_by_id(company_id)
    return SuccessResponse(data=data)


@router.patch("/{company_id}", response_model=SuccessResponse, summary="Update company")
def update_company_by_id(
    company_id: UUID,
    payload: CompanyUpdate,
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    data = svc.update(company_id, payload, ctx)
    return SuccessResponse(data=data)


@router.delete("/{company_id}", response_model=MessageResponse, summary="Delete company")
def delete_company(
    company_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    svc.soft_delete(company_id, ctx)
    return MessageResponse(message="Company deleted.")

