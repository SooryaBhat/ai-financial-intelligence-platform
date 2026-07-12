"""Customers router."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1._crud_factory import make_crud_router
from app.dependencies.auth import get_request_context
from app.repositories.customers import CustomerRepository
from app.schemas.common import SuccessResponse
from app.schemas.customers import CustomerCreate, CustomerUpdate
from app.services.context import RequestContext

router = make_crud_router(
    prefix="/customers",
    tag="Customers",
    repo_class=CustomerRepository,
    create_schema=CustomerCreate,
    update_schema=CustomerUpdate,
)


# Extend with search endpoint
@router.get("/search", response_model=SuccessResponse, summary="Search customers")
def search_customers(
    q: str = Query(..., min_length=1),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = CustomerRepository(ctx.user_client)
    data = repo.search(ctx.company_id, q)
    return SuccessResponse(data=data)
