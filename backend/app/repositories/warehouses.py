"""Warehouses repository."""
from supabase import Client
from app.repositories.base import BaseRepository


class WarehouseRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "warehouses")
