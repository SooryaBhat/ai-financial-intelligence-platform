"""Predictions router — /api/v1/predictions"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.predictions import PredictionLogRepository, PredictionRepository
from app.schemas.common import SuccessResponse
from app.schemas.predictions import PredictionCreate, PredictionUpdate
from app.services.context import RequestContext

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/", response_model=SuccessResponse, summary="List predictions")
def list_predictions(
    prediction_type: str = Query(None),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = PredictionRepository(ctx.user_client)
    if prediction_type:
        data = repo.list_by_type(ctx.company_id, prediction_type)
    else:
        data = repo.list(ctx.company_id)
    return SuccessResponse(data=data)


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create prediction request")
def create_prediction(payload: PredictionCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = PredictionRepository(ctx.user_client)
    data = {
        "company_id": str(ctx.company_id),
        "ml_model_id": str(payload.ml_model_id) if payload.ml_model_id else None,
        "prediction_type": payload.prediction_type.value,
        "period_start": payload.period_start.isoformat() if payload.period_start else None,
        "period_end": payload.period_end.isoformat() if payload.period_end else None,
        "input_data": payload.input_data,
        "status": "pending",
    }
    result = repo.create(data)
    return SuccessResponse(data=result)


@router.get("/{prediction_id}", response_model=SuccessResponse, summary="Get prediction")
def get_prediction(prediction_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = PredictionRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(prediction_id, ctx.company_id))


@router.patch("/{prediction_id}", response_model=SuccessResponse, summary="Update prediction (backfill actual value)")
def update_prediction(
    prediction_id: UUID,
    payload: PredictionUpdate,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = PredictionRepository(ctx.user_client)
    data = repo.update(prediction_id, payload.model_dump(exclude_none=True), ctx.company_id)
    return SuccessResponse(data=data)


@router.get("/{prediction_id}/logs", response_model=SuccessResponse, summary="Get prediction logs")
def get_logs(prediction_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = PredictionLogRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_for_prediction(prediction_id))
