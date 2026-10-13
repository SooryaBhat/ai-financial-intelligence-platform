"""
Companies service — business logic for company management.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.exceptions import ConflictError, NotFoundError
from app.repositories.companies import CompanyRepository
from app.schemas.companies import CompanyCreate, CompanyUpdate
from app.services.audit import audit_service
from app.services.context import RequestContext


class CompanyService:
    def __init__(self, repo: CompanyRepository) -> None:
        self._repo = repo

    def get(self, company_id: UUID, ctx: RequestContext) -> Dict[str, Any]:
        result = self._repo.get_with_plan(company_id)
        if not result:
            raise NotFoundError("Company", str(company_id))
        return result

    def get_by_id(self, company_id: UUID) -> Dict[str, Any]:
        result = self._repo.get_by_id(company_id)
        if not result:
            raise NotFoundError("Company", str(company_id))
        return result

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        items = self._repo.list_companies(
            search_column="name" if search else None,
            search_value=search,
            limit=page_size,
            offset=offset,
        )
        total = self._repo.count_companies(
            search_column="name" if search else None,
            search_value=search,
        )
        import math
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        }

    def create(self, data: CompanyCreate, ctx: RequestContext) -> Dict[str, Any]:
        dump = data.model_dump(exclude_none=True)
        if "slug" not in dump or not dump["slug"]:
            dump["slug"] = dump["name"].lower().replace(" ", "-")
        created = self._repo.create(dump)
        audit_service.log_create(
            ctx.company_id, "company", UUID(created["id"]),
            created, ctx.user_id, ctx.ip_address, ctx.user_agent,
        )
        return created

    def list_all(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        return self._repo.list_all(limit=limit, offset=offset)

    def update(self, company_id: UUID, data: CompanyUpdate, ctx: RequestContext) -> Dict[str, Any]:
        old = self._repo.get_by_id(company_id)
        updated = self._repo.update(company_id, data.model_dump(exclude_none=True))
        audit_service.log_update(ctx.company_id, "company", company_id,
                                  old, updated, ctx.user_id, ctx.ip_address, ctx.user_agent)
        return updated

    def soft_delete(self, company_id: UUID, ctx: RequestContext) -> bool:
        old = self._repo.get_by_id(company_id)
        result = self._repo.soft_delete(company_id)
        audit_service.log_delete(ctx.company_id, "company", company_id,
                                  old, ctx.user_id, ctx.ip_address, ctx.user_agent)
        return result

