"""Exceptions raised by the football-data.org API client."""

from __future__ import annotations


class FootballDataError(Exception):
    """Base exception for all football-data.org client errors."""


class FootballDataAuthError(FootballDataError):
    """Raised on 400/403 - invalid or missing API key."""


class FootballDataNotFoundError(FootballDataError):
    """Raised on 404 - resource does not exist (e.g. unknown competition/season)."""


class FootballDataRateLimitError(FootballDataError):
    """Raised on 429 after retries are exhausted."""


class FootballDataServerError(FootballDataError):
    """Raised on 5xx after retries are exhausted."""


class FootballDataSchemaError(FootballDataError):
    """Raised when a response doesn't match the expected shape."""
