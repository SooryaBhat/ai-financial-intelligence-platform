"""Integrations router — /api/v1/integrations"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1._crud_factory import make_crud_router
from app.dependencies.auth import get_request_context
from app.repositories.integrations import IntegrationRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.integrations import IntegrationCreate, IntegrationUpdate
from app.services.context import RequestContext

router = make_crud_router(
    prefix="/integrations",
    tag="Integrations",
    repo_class=IntegrationRepository,
    create_schema=IntegrationCreate,
    update_schema=IntegrationUpdate,
    search_column="name",
)
