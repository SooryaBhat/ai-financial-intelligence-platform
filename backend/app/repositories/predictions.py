"""Predictions and prediction logs repository."""
from typing import Any, Dict, List
from uuid import UUID

from supabase import Client

from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "predictions")

    def list_by_type(self, company_id: UUID, prediction_type: str) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("company_id", str(company_id))
            .eq("prediction_type", prediction_type)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []


class PredictionLogRepository(BaseRepository):
    def __init__(self, client: Client) -> None:
        super().__init__(client, "prediction_logs")

    def list_for_prediction(self, prediction_id: UUID) -> List[Dict[str, Any]]:
        response = (
            self._query()
            .select("*")
            .eq("prediction_id", str(prediction_id))
            .order("created_at")
            .execute()
        )
        return response.data or []

    def create_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._query().insert(data).execute()
        return response.data[0] if response.data else {}
