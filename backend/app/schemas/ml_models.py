"""ML Models schemas."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import ModelType
from app.schemas.common import AppBaseModel, TimestampMixin


class MLModelBase(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    model_type: ModelType
    target_metric: Optional[str] = None
    algorithm: Optional[str] = None
    version: Optional[str] = None
    storage_path: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = {}


class MLModelCreate(MLModelBase):
    company_id: Optional[UUID] = None  # NULL = platform-wide


class MLModelUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    version: Optional[str] = None
    storage_path: Optional[str] = None
    accuracy_score: Optional[float] = Field(None, ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None


class MLModelResponse(MLModelBase, TimestampMixin):
    id: UUID
    company_id: Optional[UUID] = None
    trained_at: Optional[datetime] = None
    accuracy_score: Optional[float] = None
