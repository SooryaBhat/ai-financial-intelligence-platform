"""
Companies service — business logic for company management.
"""
from typing import Any, Dict, List
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
