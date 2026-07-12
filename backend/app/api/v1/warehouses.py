"""Warehouses router."""
from app.api.v1._crud_factory import make_crud_router
from app.repositories.warehouses import WarehouseRepository
from app.schemas.warehouses import WarehouseCreate, WarehouseUpdate

router = make_crud_router(
    prefix="/warehouses",
    tag="Warehouses",
    repo_class=WarehouseRepository,
    create_schema=WarehouseCreate,
    update_schema=WarehouseUpdate,
)
