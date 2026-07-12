"""ML Models router — /api/v1/ml-models"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_request_context
from app.repositories.ml_models import MLModelRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.ml_models import MLModelCreate, MLModelUpdate
from app.services.context import RequestContext

router = APIRouter(prefix="/ml-models", tags=["ML Models"])


@router.get("/", response_model=SuccessResponse, summary="List available ML models")
def list_models(ctx: RequestContext = Depends(get_request_context)):
    repo = MLModelRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_available(ctx.company_id))


@router.get("/{model_id}", response_model=SuccessResponse, summary="Get ML model")
def get_model(model_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = MLModelRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(model_id))


@router.patch("/{model_id}", response_model=SuccessResponse, summary="Update ML model metadata")
def update_model(model_id: UUID, payload: MLModelUpdate, ctx: RequestContext = Depends(get_request_context)):
    repo = MLModelRepository(ctx.user_client)
    data = repo.update(model_id, payload.model_dump(exclude_none=True))
    return SuccessResponse(data=data)
