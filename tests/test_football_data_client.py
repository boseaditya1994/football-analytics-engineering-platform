"""Unit tests for FootballDataClient. All HTTP calls are mocked - no live API calls."""

from __future__ import annotations

import httpx
import pytest
import respx

from football_pipeline.api import (
    FootballDataAuthError,
    FootballDataClient,
    FootballDataNotFoundError,
    FootballDataRateLimitError,
    FootballDataSchemaError,
    FootballDataServerError,
)

BASE_URL = "https://api.football-data.org/v4"


@pytest.fixture
def client() -> FootballDataClient:
    c = FootballDataClient(
        api_key="test-key",
        base_url=BASE_URL,
        max_calls_per_minute=1000,
        retry_attempts=3,
        retry_min_wait_seconds=0.01,
        retry_max_wait_seconds=0.05,
    )
    yield c
    c.close()


@respx.mock
def test_get_competition_success(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL").mock(
        return_value=httpx.Response(200, json={"id": 2021, "code": "PL", "name": "Premier League"})
    )
    result = client.get_competition("PL")
    assert result["code"] == "PL"
    assert result["name"] == "Premier League"


@respx.mock
def test_get_matches_empty_response(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL/matches").mock(
        return_value=httpx.Response(200, json={"count": 0, "matches": []})
    )
    matches = client.get_matches("PL", season="2025")
    assert matches == []


@respx.mock
def test_get_teams_timeout_raises(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL/teams").mock(side_effect=httpx.TimeoutException("timed out"))
    with pytest.raises(httpx.TimeoutException):
        client.get_teams("PL")


@respx.mock
def test_get_competition_auth_error(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL").mock(
        return_value=httpx.Response(403, json={"message": "invalid token"})
    )
    with pytest.raises(FootballDataAuthError):
        client.get_competition("PL")


@respx.mock
def test_get_competition_not_found(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/ZZ").mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    with pytest.raises(FootballDataNotFoundError):
        client.get_competition("ZZ")


@respx.mock
def test_rate_limit_retries_then_succeeds(client: FootballDataClient) -> None:
    route = respx.get(f"{BASE_URL}/competitions/PL")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "0"}, json={"message": "rate limited"}),
        httpx.Response(200, json={"id": 2021, "code": "PL", "name": "Premier League"}),
    ]
    result = client.get_competition("PL")
    assert result["code"] == "PL"
    assert route.call_count == 2


@respx.mock
def test_rate_limit_exhausted_raises(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"}, json={"message": "rate limited"})
    )
    with pytest.raises(FootballDataRateLimitError):
        client.get_competition("PL")


@respx.mock
def test_server_error_retries_then_raises(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL").mock(
        return_value=httpx.Response(500, json={"message": "server error"})
    )
    with pytest.raises(FootballDataServerError):
        client.get_competition("PL")


@respx.mock
def test_malformed_response_raises_schema_error(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"})
    )
    with pytest.raises(FootballDataSchemaError):
        client.get_competition("PL")


@respx.mock
def test_get_standings_success(client: FootballDataClient) -> None:
    respx.get(f"{BASE_URL}/competitions/PL/standings").mock(
        return_value=httpx.Response(
            200,
            json={
                "competition": {"code": "PL"},
                "season": {"id": 1},
                "standings": [{"stage": "REGULAR_SEASON", "table": []}],
            },
        )
    )
    result = client.get_standings("PL", season="2025")
    assert result["standings"][0]["stage"] == "REGULAR_SEASON"


@respx.mock
def test_matchday_and_status_params_forwarded(client: FootballDataClient) -> None:
    route = respx.get(f"{BASE_URL}/competitions/PL/matches").mock(
        return_value=httpx.Response(200, json={"count": 0, "matches": []})
    )
    client.get_matches("PL", matchday=5, status="FINISHED")
    sent_request = route.calls.last.request
    assert "matchday=5" in str(sent_request.url)
    assert "status=FINISHED" in str(sent_request.url)
