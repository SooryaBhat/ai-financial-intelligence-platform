"""
Companies router — /api/v1/companies
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.companies import CompanyRepository
from app.schemas.common import MessageResponse, PaginatedResponse, SuccessResponse
from app.schemas.companies import CompanyResponse, CompanyUpdate
from app.services.companies import CompanyService
from app.services.context import RequestContext

router = APIRouter(prefix="/companies", tags=["Companies"])


def _get_service(ctx: RequestContext = Depends(get_request_context)) -> CompanyService:
    return CompanyService(CompanyRepository(ctx.user_client))


@router.get(
    "/me",
    response_model=SuccessResponse,
    summary="Get the current company",
)
def get_company(
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
def update_company(
    payload: CompanyUpdate,
    ctx: RequestContext = Depends(get_request_context),
    svc: CompanyService = Depends(_get_service),
):
    data = svc.update(ctx.company_id, payload, ctx)
    return SuccessResponse(data=data)
