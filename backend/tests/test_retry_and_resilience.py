"""
Tests for Supabase query execution resilience, transient error retry,
and LoggingMiddleware exception containment.
"""
from unittest.mock import MagicMock
import httpx
import pytest

from app.database.retry import execute_with_retry


def test_execute_with_retry_succeeds_first_try():
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(data=[{"id": 1}])

    res = execute_with_retry(mock_query, max_retries=3)
    assert res.data == [{"id": 1}]
    assert mock_query.execute.call_count == 1


def test_execute_with_retry_recovers_from_transient_disconnect():
    mock_query = MagicMock()
    # First call raises RemoteProtocolError (Server disconnected), second call succeeds
    mock_query.execute.side_effect = [
        httpx.RemoteProtocolError("Server disconnected"),
        MagicMock(data=[{"id": 2}]),
    ]

    res = execute_with_retry(mock_query, max_retries=3, initial_delay=0.01)
    assert res.data == [{"id": 2}]
    assert mock_query.execute.call_count == 2


def test_execute_with_retry_exhausts_and_raises():
    mock_query = MagicMock()
    mock_query.execute.side_effect = httpx.RemoteProtocolError("Server disconnected")

    with pytest.raises(httpx.RemoteProtocolError):
        execute_with_retry(mock_query, max_retries=2, initial_delay=0.01)
    assert mock_query.execute.call_count == 2


def test_execute_with_retry_callable():
    calls = []
    def flaky_func():
        calls.append(1)
        if len(calls) < 2:
            raise httpx.ConnectError("Connection failed")
        return "success"

    res = execute_with_retry(flaky_func, max_retries=3, initial_delay=0.01)
    assert res == "success"
    assert len(calls) == 2
