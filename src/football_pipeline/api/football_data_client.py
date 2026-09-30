"""Client for the football-data.org v4 API.

Free-tier constraints this client is built around:
- 10 requests/minute (enforced client-side via RateLimiter, not just relied on server-side)
- 429 responses include a Retry-After header, which we honor
- No pagination on the endpoints we use (competitions/teams/matches/standings
  are returned in full per call)
"""

from __future__ import annotations

from typing import Self

import httpx
import structlog
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from football_pipeline.api.exceptions import (
    FootballDataAuthError,
    FootballDataError,
    FootballDataNotFoundError,
    FootballDataRateLimitError,
    FootballDataSchemaError,
    FootballDataServerError,
)
from football_pipeline.api.rate_limiter import RateLimiter
from football_pipeline.api.schemas import (
    CompetitionEnvelope,
    MatchListEnvelope,
    StandingsEnvelope,
    TeamListEnvelope,
)

logger = structlog.get_logger(__name__)

_RETRYABLE_EXCEPTIONS = (FootballDataRateLimitError, FootballDataServerError, httpx.TimeoutException)


class FootballDataClient:
    """Thin, retrying, rate-limited wrapper around the football-data.org v4 API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.football-data.org/v4",
        timeout_seconds: float = 15.0,
        max_calls_per_minute: int = 10,
        transport: httpx.BaseTransport | None = None,
        retry_attempts: int = 5,
        retry_min_wait_seconds: float = 2.0,
        retry_max_wait_seconds: float = 60.0,
    ) -> None:
        self._rate_limiter = RateLimiter(max_calls=max_calls_per_minute, period_seconds=60.0)
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-Auth-Token": api_key},
            timeout=timeout_seconds,
            transport=transport,
        )
        self._retrying_get = retry(
            retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
            stop=stop_after_attempt(retry_attempts),
            wait=wait_exponential(multiplier=1, min=retry_min_wait_seconds, max=retry_max_wait_seconds),
            reraise=True,
        )(self._get_once)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- Public entity methods -------------------------------------------------

    def get_competition(self, competition_code: str) -> dict:
        payload = self._get(f"/competitions/{competition_code}")
        return self._validate(CompetitionEnvelope, payload).model_dump()

    def get_teams(self, competition_code: str, season: str | None = None) -> list[dict]:
        params = {"season": season} if season else None
        payload = self._get(f"/competitions/{competition_code}/teams", params=params)
        envelope = self._validate(TeamListEnvelope, payload)
        return envelope.teams

    def get_matches(
        self,
        competition_code: str,
        season: str | None = None,
        matchday: int | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        params = {
            k: v
            for k, v in {
                "season": season,
                "matchday": matchday,
                "status": status,
                "dateFrom": date_from,
                "dateTo": date_to,
            }.items()
            if v is not None
        }
        payload = self._get(f"/competitions/{competition_code}/matches", params=params or None)
        envelope = self._validate(MatchListEnvelope, payload)
        return envelope.matches

    def get_standings(self, competition_code: str, season: str | None = None) -> dict:
        params = {"season": season} if season else None
        payload = self._get(f"/competitions/{competition_code}/standings", params=params)
        return self._validate(StandingsEnvelope, payload).model_dump()

    # -- Internals ---------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict:
        return self._retrying_get(path, params)

    def _get_once(self, path: str, params: dict | None = None) -> dict:
        self._rate_limiter.acquire()
        logger.info("football_data_request", path=path, params=params)
        try:
            response = self._client.get(path, params=params)
        except httpx.TimeoutException:
            logger.warning("football_data_timeout", path=path)
            raise

        if response.status_code == 200:
            return response.json()
        if response.status_code in (400, 403):
            raise FootballDataAuthError(f"{response.status_code} for {path}: {response.text}")
        if response.status_code == 404:
            raise FootballDataNotFoundError(f"404 for {path}: {response.text}")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            logger.warning("football_data_rate_limited", path=path, retry_after=retry_after)
            raise FootballDataRateLimitError(f"429 for {path}, retry-after={retry_after}")
        if response.status_code >= 500:
            raise FootballDataServerError(f"{response.status_code} for {path}: {response.text}")

        raise FootballDataError(f"Unexpected status {response.status_code} for {path}: {response.text}")

    @staticmethod
    def _validate(model_cls: type, payload: dict):
        try:
            return model_cls.model_validate(payload)
        except ValidationError as exc:
            raise FootballDataSchemaError(f"Response failed schema validation: {exc}") from exc
