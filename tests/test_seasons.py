from datetime import date

import pytest

from football_pipeline.utils.seasons import (
    current_season_start_year,
    is_current_season,
    season_range,
)


def test_current_season_before_july_rollover() -> None:
    assert current_season_start_year(date(2026, 5, 1)) == 2025


def test_current_season_after_july_rollover() -> None:
    assert current_season_start_year(date(2026, 8, 1)) == 2026


def test_current_season_on_rollover_month() -> None:
    assert current_season_start_year(date(2026, 7, 1)) == 2026


def test_season_range_inclusive() -> None:
    assert season_range(2018, 2021) == [2018, 2019, 2020, 2021]


def test_season_range_defaults_to_current_season() -> None:
    result = season_range(2024, end_year=current_season_start_year(date(2026, 9, 28)))
    assert result[-1] == current_season_start_year(date(2026, 9, 28))


def test_season_range_rejects_start_after_end() -> None:
    with pytest.raises(ValueError):
        season_range(2025, 2020)


def test_is_current_season() -> None:
    today = date(2026, 9, 28)
    assert is_current_season(2026, today) is True
    assert is_current_season(2025, today) is False
