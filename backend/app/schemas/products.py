"""Products schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import ProductType
from app.schemas.common import AppBaseModel, TimestampMixin


class ProductBase(AppBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[UUID] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    cost_price: float = Field(default=0, ge=0)
    selling_price: float = Field(default=0, ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)
    type: ProductType = ProductType.PRODUCT
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(AppBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[UUID] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    cost_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase, TimestampMixin):
    id: UUID
    company_id: UUID
    deleted_at: Optional[datetime] = None
