"""Products router."""
from fastapi import APIRouter, Depends, Query
from app.api.v1._crud_factory import make_crud_router
from app.dependencies.auth import get_request_context
from app.repositories.products import ProductRepository
from app.schemas.common import SuccessResponse
from app.schemas.products import ProductCreate, ProductUpdate
from app.services.context import RequestContext

router = make_crud_router(
    prefix="/products",
    tag="Products",
    repo_class=ProductRepository,
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
)


@router.get("/active", response_model=SuccessResponse, summary="List all active products")
def list_active(ctx: RequestContext = Depends(get_request_context)):
    repo = ProductRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_active(ctx.company_id))


@router.get("/search", response_model=SuccessResponse, summary="Search products")
def search_products(
    q: str = Query(..., min_length=1),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = ProductRepository(ctx.user_client)
    return SuccessResponse(data=repo.search(ctx.company_id, q))
