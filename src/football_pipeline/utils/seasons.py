"""Season helpers. football-data.org identifies a season by its starting
year (e.g. season=2025 means the 2025/26 season) - the Premier League season
runs roughly August through May, so a season "rolls over" in July.
"""

from __future__ import annotations

from datetime import UTC, date, datetime


def current_season_start_year(today: date | None = None) -> int:
    today = today or datetime.now(UTC).date()
    return today.year if today.month >= 7 else today.year - 1


def season_range(start_year: int, end_year: int | None = None) -> list[int]:
    """Inclusive range of season-start years, from start_year through the
    current season by default.
    """
    end_year = end_year if end_year is not None else current_season_start_year()
    if start_year > end_year:
        raise ValueError(f"start_year ({start_year}) must be <= end_year ({end_year})")
    return list(range(start_year, end_year + 1))


def is_current_season(season_start_year: int, today: date | None = None) -> bool:
    return season_start_year == current_season_start_year(today)
