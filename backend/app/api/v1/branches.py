"""Branches router — generated via CRUD factory."""
from app.api.v1._crud_factory import make_crud_router
from app.repositories.branches import BranchRepository
from app.schemas.branches import BranchCreate, BranchUpdate

router = make_crud_router(
    prefix="/branches",
    tag="Branches",
    repo_class=BranchRepository,
    create_schema=BranchCreate,
    update_schema=BranchUpdate,
)
