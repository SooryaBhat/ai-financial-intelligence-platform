"""
RBAC dependency factory.

Usage in a router:
    from app.dependencies.rbac import require_permission

    @router.post("/invoices")
    def create_invoice(
        ctx: RequestContext = Depends(get_request_context),
        _: None = Depends(require_permission("invoices", "create")),
    ):
        ...

The require_permission dependency raises ForbiddenError if the user's role
does not include the requested resource:action permission.
"""
from typing import Callable

from fastapi import Depends

from app.dependencies.auth import get_request_context
from app.exceptions import ForbiddenError
from app.services.context import RequestContext


def require_permission(resource: str, action: str) -> Callable:
    """
    Returns a FastAPI dependency that checks if the authenticated user
    has the specified permission.

    Permissions are loaded from the DB in get_request_context() and stored
    in ctx.permissions as a list of "resource:action" strings.
    """
    def _check(ctx: RequestContext = Depends(get_request_context)) -> None:
        permission_key = f"{resource}:{action}"
        if permission_key not in ctx.permissions:
            raise ForbiddenError(
                f"Missing permission: {permission_key}. "
                f"Contact your administrator to grant access."
            )
    return _check
