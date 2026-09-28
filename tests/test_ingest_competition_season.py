from unittest.mock import MagicMock, patch

from football_pipeline.ingestion.ingest_competition_season import ingest_competition_season
from football_pipeline.utils.seasons import current_season_start_year


def make_client() -> MagicMock:
    client = MagicMock()
    client.get_teams.return_value = [{"id": 1}]
    client.get_matches.return_value = [{"id": 100, "matchday": 1}]
    client.get_standings.return_value = {"standings": []}
    return client


@patch("football_pipeline.ingestion.ingest_competition_season.run_audit")
@patch("football_pipeline.ingestion.ingest_competition_season.SnowflakeLoader")
def test_completed_historical_season_is_skipped_when_already_loaded(
    mock_loader_cls: MagicMock, mock_audit: MagicMock
) -> None:
    mock_audit.has_successful_run.return_value = True
    client = make_client()
    conn = MagicMock()

    historical_season = current_season_start_year() - 5
    results = ingest_competition_season(
        client=client,
        conn=conn,
        competition_code="PL",
        season_start_year=historical_season,
        pipeline_name="test",
    )

    assert results == {"teams": 0, "matches": 0, "standings": 0}
    client.get_teams.assert_not_called()
    client.get_matches.assert_not_called()
    client.get_standings.assert_not_called()
    mock_audit.start_run.assert_not_called()


@patch("football_pipeline.ingestion.ingest_competition_season.run_audit")
@patch("football_pipeline.ingestion.ingest_competition_season.SnowflakeLoader")
def test_completed_historical_season_ingests_when_not_already_loaded(
    mock_loader_cls: MagicMock, mock_audit: MagicMock
) -> None:
    mock_audit.has_successful_run.return_value = False
    mock_audit.start_run.return_value = MagicMock(run_id="run-123")
    client = make_client()
    conn = MagicMock()

    historical_season = current_season_start_year() - 5
    ingest_competition_season(
        client=client,
        conn=conn,
        competition_code="PL",
        season_start_year=historical_season,
        pipeline_name="test",
    )

    assert client.get_teams.called
    assert client.get_matches.called
    assert client.get_standings.called
    assert mock_audit.complete_run.call_count == 3


@patch("football_pipeline.ingestion.ingest_competition_season.run_audit")
@patch("football_pipeline.ingestion.ingest_competition_season.SnowflakeLoader")
def test_current_season_always_refreshed_even_if_already_loaded(
    mock_loader_cls: MagicMock, mock_audit: MagicMock
) -> None:
    mock_audit.has_successful_run.return_value = True  # would normally skip
    mock_audit.start_run.return_value = MagicMock(run_id="run-123")
    client = make_client()
    conn = MagicMock()

    ingest_competition_season(
        client=client,
        conn=conn,
        competition_code="PL",
        season_start_year=current_season_start_year(),
        pipeline_name="test",
    )

    # Current season is refreshed regardless of has_successful_run, since it's still in progress
    assert client.get_teams.called
    assert client.get_matches.called
    assert client.get_standings.called


@patch("football_pipeline.ingestion.ingest_competition_season.run_audit")
@patch("football_pipeline.ingestion.ingest_competition_season.SnowflakeLoader")
def test_force_flag_reingests_completed_season(
    mock_loader_cls: MagicMock, mock_audit: MagicMock
) -> None:
    mock_audit.has_successful_run.return_value = True
    mock_audit.start_run.return_value = MagicMock(run_id="run-123")
    client = make_client()
    conn = MagicMock()

    historical_season = current_season_start_year() - 5
    ingest_competition_season(
        client=client,
        conn=conn,
        competition_code="PL",
        season_start_year=historical_season,
        pipeline_name="test",
        force=True,
    )

    assert client.get_teams.called


@patch("football_pipeline.ingestion.ingest_competition_season.run_audit")
@patch("football_pipeline.ingestion.ingest_competition_season.SnowflakeLoader")
def test_failure_marks_run_failed_and_reraises(
    mock_loader_cls: MagicMock, mock_audit: MagicMock
) -> None:
    mock_audit.has_successful_run.return_value = False
    mock_audit.start_run.return_value = MagicMock(run_id="run-123")
    client = make_client()
    client.get_teams.side_effect = RuntimeError("API exploded")
    conn = MagicMock()

    try:
        ingest_competition_season(
            client=client,
            conn=conn,
            competition_code="PL",
            season_start_year=current_season_start_year() - 5,
            pipeline_name="test",
        )
        assert False, "expected RuntimeError to propagate"
    except RuntimeError:
        pass

    mock_audit.fail_run.assert_called_once()
