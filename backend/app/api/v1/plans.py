"""Plans and subscriptions router — /api/v1/plans"""
from fastapi import APIRouter, Depends

from app.dependencies.auth import get_request_context
from app.repositories.plans import PlanRepository
from app.schemas.common import SuccessResponse
from app.services.context import RequestContext

router = APIRouter(prefix="/plans", tags=["Plans & Subscriptions"])


@router.get("/", response_model=SuccessResponse, summary="List available plans")
def list_plans(ctx: RequestContext = Depends(get_request_context)):
    repo = PlanRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_active())


@router.get("/subscriptions", response_model=SuccessResponse, summary="Get company subscriptions")
def get_subscriptions(ctx: RequestContext = Depends(get_request_context)):
    repo = PlanRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_subscriptions(ctx.company_id))
