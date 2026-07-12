"""Predictions and prediction logs schemas."""
from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import (
    PredictionLogStage,
    PredictionLogStatus,
    PredictionStatus,
    PredictionType,
)
from app.schemas.common import AppBaseModel, TimestampMixin


# ── Predictions ───────────────────────────────────────────────

class PredictionCreate(AppBaseModel):
    ml_model_id: Optional[UUID] = None
    prediction_type: PredictionType
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    input_data: Dict[str, Any] = {}


class PredictionUpdate(AppBaseModel):
    predicted_value: Optional[float] = None
    actual_value: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    output_data: Optional[Dict[str, Any]] = None
    status: Optional[PredictionStatus] = None


class PredictionResponse(TimestampMixin):
    id: UUID
    company_id: UUID
    ml_model_id: Optional[UUID] = None
    prediction_type: PredictionType
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    predicted_value: Optional[float] = None
    actual_value: Optional[float] = None
    confidence_score: Optional[float] = None
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    status: PredictionStatus


# ── Prediction Logs ───────────────────────────────────────────

class PredictionLogResponse(AppBaseModel):
    id: UUID
    prediction_id: UUID
    stage: PredictionLogStage
    status: PredictionLogStatus
    message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime
