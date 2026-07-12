"""Settings router — /api/v1/settings"""
from fastapi import APIRouter, Depends

from app.dependencies.auth import get_request_context
from app.repositories.settings import SettingsRepository
from app.schemas.common import SuccessResponse
from app.schemas.settings import SettingUpsert
from app.services.context import RequestContext

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=SuccessResponse, summary="List all company settings")
def list_settings(ctx: RequestContext = Depends(get_request_context)):
    repo = SettingsRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_all(ctx.company_id))


@router.get("/{key}", response_model=SuccessResponse, summary="Get a setting by key")
def get_setting(key: str, ctx: RequestContext = Depends(get_request_context)):
    repo = SettingsRepository(ctx.user_client)
    from app.exceptions import NotFoundError
    data = repo.get_by_key(ctx.company_id, key)
    if not data:
        raise NotFoundError("Setting", key)
    return SuccessResponse(data=data)


@router.put("/{key}", response_model=SuccessResponse, summary="Upsert a setting")
def upsert_setting(
    key: str,
    payload: SettingUpsert,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = SettingsRepository(ctx.user_client)
    data = repo.upsert({
        "company_id": str(ctx.company_id),
        "key": key,
        "value": payload.value,
        "description": payload.description,
        "updated_by": str(ctx.user_id),
    })
    return SuccessResponse(data=data)
