"""Categories router."""
from fastapi import APIRouter, Depends, Query
from app.api.v1._crud_factory import make_crud_router
from app.dependencies.auth import get_request_context
from app.repositories.categories import CategoryRepository
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.schemas.common import SuccessResponse
from app.services.context import RequestContext

router = make_crud_router(
    prefix="/categories",
    tag="Categories",
    repo_class=CategoryRepository,
    create_schema=CategoryCreate,
    update_schema=CategoryUpdate,
)


@router.get("/by-type/{category_type}", response_model=SuccessResponse, summary="List categories by type")
def list_by_type(
    category_type: str,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = CategoryRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_by_type(ctx.company_id, category_type))
