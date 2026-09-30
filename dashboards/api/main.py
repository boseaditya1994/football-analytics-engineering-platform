"""Read-only FastAPI backend for the React dashboard.

Queries the MARTS/AUDIT schemas in Snowflake and returns JSON. The React
frontend never talks to Snowflake directly - credentials stay server-side,
read from the same .env the ingestion pipeline uses.

Run: uvicorn dashboards.api.main:app --reload --port 8000
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from football_pipeline.config.settings import get_settings
from football_pipeline.loaders.snowflake_loader import connect

app = FastAPI(title="Football Analytics Dashboard API")

# Local dev origins are always allowed; production frontend origin(s) come
# from ALLOWED_ORIGINS (comma-separated), e.g. "https://my-app.vercel.app".
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    # Vercel gives every preview deploy its own subdomain - allow all of
    # them for a given project rather than hardcoding one URL that goes
    # stale on the next preview.
    allow_origin_regex=os.environ.get("ALLOWED_ORIGIN_REGEX"),
    allow_methods=["GET"],
    allow_headers=["*"],
)


@contextmanager
def get_cursor():
    settings = get_settings()
    conn = connect(settings)
    try:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    finally:
        conn.close()


def _rows_as_dicts(cursor) -> list[dict[str, Any]]:
    columns = [col[0].lower() for col in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _run(cursor, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cursor.execute(sql, params)
    return _rows_as_dicts(cursor)


def _query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Single-query convenience wrapper - opens and closes its own connection.
    For endpoints running multiple queries, open one connection with
    get_cursor() and call _run(cursor, ...) per query instead, to avoid a
    separate auth handshake per query.
    """
    with get_cursor() as cursor:
        return _run(cursor, sql, params)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/seasons")
def list_seasons() -> list[dict[str, Any]]:
    return _query(
        """
        SELECT season, season_start_date, season_end_date, total_matchweeks
        FROM MARTS.dim_season
        ORDER BY season DESC
        """
    )


@app.get("/api/teams")
def list_teams() -> list[dict[str, Any]]:
    return _query(
        """
        SELECT team_id, team_name, team_short_name, team_tla, team_crest_url
        FROM MARTS.dim_team
        ORDER BY team_name
        """
    )


@app.get("/api/league-table")
def league_table(season: str = Query(...)) -> list[dict[str, Any]]:
    rows = _query(
        """
        SELECT team_id, team_name, team_crest_url, league_position, played_games,
               won, drawn, lost, goals_for, goals_against, goal_difference,
               points, points_per_game, form_last_5
        FROM MARTS.mart_league_table
        WHERE season = %s
        ORDER BY league_position
        """,
        (season,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No league table for season {season}")
    return rows


@app.get("/api/progression")
def league_progression(
    season: str = Query(...), team_ids: str | None = Query(None)
) -> list[dict[str, Any]]:
    sql = """
        SELECT p.team_id, t.team_name, p.matchweek, p.league_position, p.points,
               p.position_change
        FROM MARTS.mart_league_progression p
        JOIN MARTS.dim_team t ON t.team_id = p.team_id
        WHERE p.season = %s
    """
    params: list[Any] = [season]
    if team_ids:
        ids = [int(x) for x in team_ids.split(",") if x.strip()]
        placeholders = ",".join(["%s"] * len(ids))
        sql += f" AND p.team_id IN ({placeholders})"
        params.extend(ids)
    sql += " ORDER BY p.team_id, p.matchweek"
    return _query(sql, tuple(params))


@app.get("/api/team-form")
def team_form(team_id: int = Query(...), season: str = Query(...)) -> list[dict[str, Any]]:
    return _query(
        """
        SELECT match_id, matchweek, kickoff_utc, result, points, ppg_last_5,
               ppg_last_10, form_last_5
        FROM MARTS.mart_team_form
        WHERE team_id = %s AND season = %s
        ORDER BY kickoff_utc
        """,
        (team_id, season),
    )


@app.get("/api/home-away")
def home_away(season: str = Query(...)) -> list[dict[str, Any]]:
    return _query(
        """
        SELECT h.team_id, t.team_name, h.home_played, h.home_points, h.home_ppg,
               h.home_win_pct, h.home_goal_difference,
               h.away_played, h.away_points, h.away_ppg,
               h.away_win_pct, h.away_goal_difference
        FROM MARTS.mart_home_away_performance h
        JOIN MARTS.dim_team t ON t.team_id = h.team_id
        WHERE h.season = %s
        ORDER BY h.home_ppg DESC
        """,
        (season,),
    )


@app.get("/api/goal-analysis")
def goal_analysis(season: str = Query(...)) -> list[dict[str, Any]]:
    return _query(
        """
        SELECT g.team_id, t.team_name, g.played, g.goals_for, g.goals_against,
               g.goals_for_per_match, g.goals_against_per_match,
               g.clean_sheets, g.clean_sheet_pct,
               g.matches_failed_to_score, g.failed_to_score_pct
        FROM MARTS.mart_goal_analysis g
        JOIN MARTS.dim_team t ON t.team_id = g.team_id
        WHERE g.season = %s
        ORDER BY g.goals_for DESC
        """,
        (season,),
    )


@app.get("/api/pipeline-health")
def pipeline_health() -> dict[str, Any]:
    with get_cursor() as cursor:
        recent_runs = _run(
            cursor,
            """
            SELECT run_id, pipeline_name, dataset, competition_code, season, status,
                   started_at, completed_at, records_received, records_inserted,
                   records_rejected, error_message
            FROM AUDIT.PIPELINE_RUN_AUDIT
            ORDER BY started_at DESC
            LIMIT 20
            """,
        )
        summary = _run(
            cursor,
            """
            SELECT
                COUNT(*) AS total_runs,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_runs,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs,
                SUM(records_inserted) AS total_records_inserted,
                MAX(CASE WHEN status = 'SUCCESS' THEN completed_at END) AS last_success_at
            FROM AUDIT.PIPELINE_RUN_AUDIT
            """,
        )
        dq_summary = _run(
            cursor,
            """
            SELECT COUNT(*) AS total_checks,
                   SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failed_checks
            FROM AUDIT.DATA_QUALITY_AUDIT
            """,
        )
    return {
        "recent_runs": recent_runs,
        "summary": summary[0] if summary else {},
        "data_quality": dq_summary[0] if dq_summary else {},
    }
