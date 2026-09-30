from unittest.mock import MagicMock

from football_pipeline.audit.reconcile import run_reconciliation


def make_conn_with_rows(rows: list[tuple], columns: list[str]) -> MagicMock:
    conn = MagicMock()
    select_cursor = MagicMock()
    select_cursor.description = [(c,) for c in columns]
    select_cursor.fetchall.return_value = rows
    insert_cursor = MagicMock()
    conn.cursor.side_effect = [select_cursor, insert_cursor]
    return conn


COLUMNS = [
    "season",
    "matchweek",
    "team_id",
    "team_name",
    "api_position",
    "derived_position",
    "api_points",
    "derived_points",
    "api_goal_difference",
    "derived_goal_difference",
]


def test_no_rows_returns_zero_mismatches() -> None:
    conn = make_conn_with_rows([], COLUMNS)
    result = run_reconciliation(conn, competition_code="PL")
    assert result == 0


def test_matching_row_produces_zero_mismatches() -> None:
    rows = [("2023", 38, 65, "Manchester City FC", 1, 1, 91, 91, 62, 62)]
    conn = make_conn_with_rows(rows, COLUMNS)
    result = run_reconciliation(conn, competition_code="PL")
    assert result == 0


def test_mismatched_points_is_detected() -> None:
    rows = [("2023", 38, 65, "Manchester City FC", 1, 1, 91, 88, 62, 62)]
    conn = make_conn_with_rows(rows, COLUMNS)
    result = run_reconciliation(conn, competition_code="PL")
    assert result == 1


def test_multiple_mismatches_on_one_row_all_counted() -> None:
    rows = [("2023", 38, 65, "Manchester City FC", 1, 2, 91, 88, 62, 60)]
    conn = make_conn_with_rows(rows, COLUMNS)
    result = run_reconciliation(conn, competition_code="PL")
    assert result == 3


def test_writes_one_audit_row_per_check() -> None:
    rows = [("2023", 38, 65, "Manchester City FC", 1, 1, 91, 91, 62, 62)]
    select_cursor = MagicMock()
    select_cursor.description = [(c,) for c in COLUMNS]
    select_cursor.fetchall.return_value = rows
    insert_cursor = MagicMock()
    conn = MagicMock()
    conn.cursor.side_effect = [select_cursor, insert_cursor]

    run_reconciliation(conn, competition_code="PL")

    # One check per (position, points, goal_difference) = 3 audit inserts
    assert insert_cursor.execute.call_count == 3
