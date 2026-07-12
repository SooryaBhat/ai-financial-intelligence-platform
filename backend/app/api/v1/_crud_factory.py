"""Generic CRUD router factory.
Reused to build identical CRUD routers for simple entities.
"""
from typing import Any, Callable, Dict, Type
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_request_context
from app.repositories.base import BaseRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.services.context import RequestContext


def make_crud_router(
    prefix: str,
    tag: str,
    repo_class: Type[BaseRepository],
    create_schema,
    update_schema,
    search_column: str = "name",
) -> APIRouter:
    """
    Factory that creates a standard CRUD APIRouter for a simple entity.
    Reduces boilerplate for entities without complex business logic.
    """
    router = APIRouter(prefix=prefix, tags=[tag])

    def _repo(ctx: RequestContext = Depends(get_request_context)) -> BaseRepository:
        return repo_class(ctx.user_client)

    @router.get("/", response_model=SuccessResponse, summary=f"List {tag}")
    def list_items(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str = Query(None),
        ctx: RequestContext = Depends(get_request_context),
        repo: BaseRepository = Depends(_repo),
    ):
        offset = (page - 1) * page_size
        data = repo.list(
            ctx.company_id,
            search_column=search_column if search else None,
            search_value=search,
            limit=page_size,
            offset=offset,
        )
        total = repo.count(ctx.company_id)
        import math
        return SuccessResponse(data={
            "items": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        })

    @router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary=f"Create {tag}")
    def create_item(
        payload: create_schema,
        ctx: RequestContext = Depends(get_request_context),
        repo: BaseRepository = Depends(_repo),
    ):
        data = payload.model_dump(exclude_none=True)
        data["company_id"] = str(ctx.company_id)
        result = repo.create(data)
        return SuccessResponse(data=result)

    @router.get("/{item_id}", response_model=SuccessResponse, summary=f"Get {tag} by ID")
    def get_item(
        item_id: UUID,
        ctx: RequestContext = Depends(get_request_context),
        repo: BaseRepository = Depends(_repo),
    ):
        data = repo.get_by_id(item_id, ctx.company_id)
        return SuccessResponse(data=data)

    @router.patch("/{item_id}", response_model=SuccessResponse, summary=f"Update {tag}")
    def update_item(
        item_id: UUID,
        payload: update_schema,
        ctx: RequestContext = Depends(get_request_context),
        repo: BaseRepository = Depends(_repo),
    ):
        data = repo.update(item_id, payload.model_dump(exclude_none=True), ctx.company_id)
        return SuccessResponse(data=data)

    @router.delete("/{item_id}", response_model=MessageResponse, summary=f"Delete {tag}")
    def delete_item(
        item_id: UUID,
        ctx: RequestContext = Depends(get_request_context),
        repo: BaseRepository = Depends(_repo),
    ):
        repo.soft_delete(item_id, ctx.company_id)
        return MessageResponse(message=f"{tag} deleted.")

    return router
