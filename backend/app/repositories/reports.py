"""Reports repository."""
from supabase import Client
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "reports")
