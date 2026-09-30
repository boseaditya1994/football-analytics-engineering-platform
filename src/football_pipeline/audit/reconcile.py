"""League-table reconciliation: compares the API's own reported standings
(STAGING.stg_standings) against our independently-derived standings
(MARTS.fact_standing_snapshot), writes every row's match/mismatch outcome to
AUDIT.RECONCILIATION_AUDIT, and exits non-zero if any mismatch is found so
CI/the scheduled pipeline surfaces it loudly rather than silently.

Usage:
    python -m football_pipeline.audit.reconcile --competition PL
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime

import snowflake.connector
import structlog

from football_pipeline.config.settings import get_settings
from football_pipeline.loaders.snowflake_loader import connect
from football_pipeline.utils.logging import configure_logging

logger = structlog.get_logger(__name__)

_RECONCILE_SQL = """
-- stg_standings is a snapshot of the API's CURRENT reported table - it has
-- no matchweek column, only played_games. For a given team, played_games IS
-- the matchweek number that team has completed, so that's the correct join
-- key into fact_standing_snapshot (rather than assuming every team is on
-- the same round, which postponements can break).
with standings as (
    select * from STAGING.stg_standings where competition_code = %s
)
select
    s.season,
    s.played_games as matchweek,
    s.team_id,
    t.team_name,
    s.api_position,
    f.league_position as derived_position,
    s.points as api_points,
    f.points as derived_points,
    s.goal_difference as api_goal_difference,
    f.goal_difference as derived_goal_difference
from standings s
join MARTS.fact_standing_snapshot f
  on f.team_id = s.team_id and f.season = s.season and f.matchweek = s.played_games
join MARTS.dim_team t on t.team_id = s.team_id
"""


def run_reconciliation(
    conn: snowflake.connector.SnowflakeConnection, competition_code: str
) -> int:
    """Returns the number of mismatched rows found."""
    cursor = conn.cursor()
    try:
        cursor.execute(_RECONCILE_SQL, (competition_code,))
        columns = [c[0].lower() for c in cursor.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        cursor.close()

    if not rows:
        logger.warning("reconciliation_no_rows", competition_code=competition_code)
        return 0

    mismatch_count = 0
    audit_rows = []
    executed_at = datetime.now(UTC).isoformat()

    for row in rows:
        checks = {
            "position": (row["api_position"], row["derived_position"]),
            "points": (row["api_points"], row["derived_points"]),
            "goal_difference": (row["api_goal_difference"], row["derived_goal_difference"]),
        }
        for check_name, (source_value, derived_value) in checks.items():
            is_match = source_value == derived_value
            if not is_match:
                mismatch_count += 1
                logger.warning(
                    "reconciliation_mismatch",
                    season=row["season"],
                    matchweek=row["matchweek"],
                    team=row["team_name"],
                    check=check_name,
                    api_value=source_value,
                    derived_value=derived_value,
                )
            audit_rows.append(
                (
                    str(uuid.uuid4()),
                    competition_code,
                    row["season"],
                    f"standings_{check_name}",
                    str(row["team_id"]),
                    json.dumps(source_value),
                    json.dumps(derived_value),
                    is_match,
                    executed_at,
                )
            )

    if audit_rows:
        insert_sql = """
            INSERT INTO AUDIT.RECONCILIATION_AUDIT
                (reconciliation_id, competition_code, season, check_name, entity_key,
                 source_value, derived_value, is_match, executed_at)
            SELECT %s, %s, %s, %s, %s, PARSE_JSON(%s), PARSE_JSON(%s), %s, %s
        """
        # One execute per row rather than executemany: PARSE_JSON(%s) mixed
        # with plain %s placeholders doesn't play well with the connector's
        # bulk paramstyle rewriting (same issue hit in snowflake_loader.py).
        cursor = conn.cursor()
        try:
            for audit_row in audit_rows:
                cursor.execute(insert_sql, audit_row)
        finally:
            cursor.close()

    logger.info(
        "reconciliation_complete",
        teams_checked=len(rows),
        checks_run=len(audit_rows),
        mismatches=mismatch_count,
    )
    return mismatch_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--competition", default="PL")
    args = parser.parse_args(argv)

    settings = get_settings()
    configure_logging(settings.log_level)

    conn = connect(settings)
    try:
        mismatch_count = run_reconciliation(conn, competition_code=args.competition)
    finally:
        conn.close()

    if mismatch_count > 0:
        logger.error("reconciliation_failed", mismatches=mismatch_count)
        return 1
    logger.info("reconciliation_passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
