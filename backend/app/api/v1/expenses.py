"""Expenses router — /api/v1/expenses"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.logging import logger
from app.dependencies.auth import get_request_context
from app.exceptions import NotFoundError, ValidationError
from app.repositories.expenses import ExpenseRepository
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.expenses import ExpenseApproveRequest, ExpenseCreate, ExpenseUpdate
from app.services.audit import audit_service
from app.services.context import RequestContext

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/", response_model=SuccessResponse, summary="List expenses")
def list_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str = Query(None, alias="status"),
    ctx: RequestContext = Depends(get_request_context),
):
    repo = ExpenseRepository(ctx.user_client)
    filters = {"status": status_filter} if status_filter else None
    data = repo.list(ctx.company_id, filters=filters, limit=page_size, offset=(page - 1) * page_size)
    return SuccessResponse(data=data)


@router.get("/pending-approval", response_model=SuccessResponse, summary="List pending expenses")
def list_pending(ctx: RequestContext = Depends(get_request_context)):
    repo = ExpenseRepository(ctx.user_client)
    return SuccessResponse(data=repo.list_pending_approval(ctx.company_id))


@router.post("/", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="Create expense")
def create_expense(payload: ExpenseCreate, ctx: RequestContext = Depends(get_request_context)):
    repo = ExpenseRepository(ctx.user_client)
    data = payload.model_dump(exclude_none=True)
    data["company_id"] = str(ctx.company_id)
    data["created_by"] = str(ctx.user_id)
    for uuid_field in ["category_id", "branch_id"]:
        if data.get(uuid_field):
            data[uuid_field] = str(data[uuid_field])
    result = repo.create(data)
    logger.info("Expense created | company={} amount={}", ctx.company_id, payload.amount)
    audit_service.log_create(
        ctx.company_id, "expense", UUID(result["id"]),
        result, ctx.user_id, ctx.ip_address, ctx.user_agent,
    )
    return SuccessResponse(data=result)


@router.get("/{expense_id}", response_model=SuccessResponse, summary="Get expense")
def get_expense(expense_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ExpenseRepository(ctx.user_client)
    return SuccessResponse(data=repo.get_by_id(expense_id, ctx.company_id))


@router.patch("/{expense_id}", response_model=SuccessResponse, summary="Update expense")
def update_expense(
    expense_id: UUID,
    payload: ExpenseUpdate,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = ExpenseRepository(ctx.user_client)
    old = repo.get_by_id(expense_id, ctx.company_id)
    data = repo.update(expense_id, payload.model_dump(exclude_none=True), ctx.company_id)
    audit_service.log_update(
        ctx.company_id, "expense", expense_id,
        old, data, ctx.user_id, ctx.ip_address, ctx.user_agent,
    )
    return SuccessResponse(data=data)


@router.post("/{expense_id}/approve", response_model=SuccessResponse, summary="Approve or reject expense")
def approve_expense(
    expense_id: UUID,
    payload: ExpenseApproveRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    repo = ExpenseRepository(ctx.user_client)
    old = repo.get_by_id(expense_id, ctx.company_id)
    data = repo.approve(expense_id, ctx.user_id, payload.status.value)
    logger.info(
        "Expense {} | expense={} company={}",
        payload.status.value, expense_id, ctx.company_id
    )
    audit_service.log_update(
        ctx.company_id, "expense", expense_id,
        {"status": old.get("status")}, {"status": payload.status.value},
        ctx.user_id, ctx.ip_address, ctx.user_agent,
    )
    return SuccessResponse(data=data)


@router.delete("/{expense_id}", response_model=MessageResponse, summary="Delete expense")
def delete_expense(expense_id: UUID, ctx: RequestContext = Depends(get_request_context)):
    repo = ExpenseRepository(ctx.user_client)
    old = repo.get_by_id(expense_id, ctx.company_id)
    repo.soft_delete(expense_id, ctx.company_id)
    audit_service.log_delete(
        ctx.company_id, "expense", expense_id,
        old, ctx.user_id, ctx.ip_address, ctx.user_agent,
    )
    return MessageResponse(message="Expense deleted.")
