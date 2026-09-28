from unittest.mock import MagicMock

from football_pipeline.loaders.snowflake_loader import SnowflakeLoader


def make_loader() -> tuple[SnowflakeLoader, MagicMock]:
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return SnowflakeLoader(conn), cursor


def test_load_competition_executes_one_insert() -> None:
    loader, cursor = make_loader()
    count = loader.load_competition(
        competition_code="PL", run_id="run-1", source="football-data.org", payload={"code": "PL"}
    )
    assert count == 1
    assert cursor.execute.call_count == 1
    sql, params = cursor.execute.call_args[0]
    assert "RAW_COMPETITIONS" in sql
    assert "PARSE_JSON" in sql
    assert params[0] == "PL"
    assert params[1] == "run-1"


def test_load_teams_executes_one_insert_per_team() -> None:
    loader, cursor = make_loader()
    teams = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}]
    count = loader.load_teams(
        competition_code="PL", season="2025", run_id="run-1", source="football-data.org", teams=teams
    )
    assert count == 3
    assert cursor.execute.call_count == 3


def test_load_teams_empty_list_skips_insert() -> None:
    loader, cursor = make_loader()
    count = loader.load_teams(
        competition_code="PL", season="2025", run_id="run-1", source="football-data.org", teams=[]
    )
    assert count == 0
    cursor.execute.assert_not_called()


def test_load_matches_uses_match_id_and_matchday() -> None:
    loader, cursor = make_loader()
    matches = [{"id": 12345, "matchday": 3}, {"id": 12346, "matchday": 3}]
    count = loader.load_matches(
        competition_code="PL",
        season="2025",
        run_id="run-1",
        source="football-data.org",
        matches=matches,
    )
    assert count == 2
    first_call_params = cursor.execute.call_args_list[0][0][1]
    # columns: competition_code, season, matchweek, match_id, run_id, source, loaded_at, raw_json
    assert first_call_params[2] == "3"  # matchweek
    assert first_call_params[3] == "12345"  # match_id


def test_load_standings_executes_one_insert() -> None:
    loader, cursor = make_loader()
    count = loader.load_standings(
        competition_code="PL",
        season="2025",
        run_id="run-1",
        source="football-data.org",
        payload={"standings": []},
    )
    assert count == 1
    cursor.execute.assert_called_once()
