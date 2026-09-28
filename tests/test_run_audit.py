from unittest.mock import MagicMock

from football_pipeline.audit import run_audit


def make_conn() -> tuple[MagicMock, MagicMock]:
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def test_start_run_inserts_running_row() -> None:
    conn, cursor = make_conn()
    ctx = run_audit.start_run(
        conn,
        pipeline_name="football_pipeline.daily",
        dataset="matches",
        source="football-data.org",
        competition_code="PL",
        season="2026",
    )
    assert ctx.run_id
    sql, params = cursor.execute.call_args[0]
    assert "PIPELINE_RUN_AUDIT" in sql
    assert "RUNNING" in sql
    assert params[0] == ctx.run_id


def test_complete_run_updates_status_success() -> None:
    conn, cursor = make_conn()
    ctx = run_audit.start_run(
        conn, pipeline_name="p", dataset="matches", source="football-data.org"
    )
    cursor.reset_mock()
    run_audit.complete_run(conn, ctx, records_received=10, records_inserted=10)
    sql, params = cursor.execute.call_args[0]
    assert "SUCCESS" in sql
    assert params[-1] == ctx.run_id


def test_fail_run_updates_status_failed_and_truncates_message() -> None:
    conn, cursor = make_conn()
    ctx = run_audit.start_run(
        conn, pipeline_name="p", dataset="matches", source="football-data.org"
    )
    cursor.reset_mock()
    long_message = "x" * 5000
    run_audit.fail_run(conn, ctx, long_message)
    sql, params = cursor.execute.call_args[0]
    assert "FAILED" in sql
    assert len(params[1]) == 4000


def test_has_successful_run_true_when_count_positive() -> None:
    conn, cursor = make_conn()
    cursor.fetchone.return_value = (1,)
    result = run_audit.has_successful_run(
        conn, dataset="matches", competition_code="PL", season="2020"
    )
    assert result is True


def test_has_successful_run_false_when_count_zero() -> None:
    conn, cursor = make_conn()
    cursor.fetchone.return_value = (0,)
    result = run_audit.has_successful_run(
        conn, dataset="matches", competition_code="PL", season="2020"
    )
    assert result is False
