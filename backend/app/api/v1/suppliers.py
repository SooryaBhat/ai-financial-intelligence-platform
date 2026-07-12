"""Suppliers router."""
from fastapi import APIRouter, Depends, Query
from app.api.v1._crud_factory import make_crud_router
from app.dependencies.auth import get_request_context
from app.repositories.suppliers import SupplierRepository
from app.schemas.common import SuccessResponse
from app.schemas.suppliers import SupplierCreate, SupplierUpdate
from app.services.context import RequestContext

router = make_crud_router(
    prefix="/suppliers",
    tag="Suppliers",
    repo_class=SupplierRepository,
    create_schema=SupplierCreate,
    update_schema=SupplierUpdate,
)


@router.get("/search", response_model=SuccessResponse, summary="Search suppliers")
def search_suppliers(
    q: str = Query(..., min_length=1),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = SupplierRepository(ctx.user_client)
    return SuccessResponse(data=repo.search(ctx.company_id, q))
