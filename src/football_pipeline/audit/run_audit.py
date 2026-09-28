"""Pipeline run audit tracking - writes to AUDIT.PIPELINE_RUN_AUDIT and
provides the idempotency check used to avoid re-ingesting immutable
historical seasons.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

import snowflake.connector
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RunContext:
    run_id: str
    pipeline_name: str
    dataset: str
    source: str
    competition_code: str | None = None
    season: str | None = None
    matchweek: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    records_received: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_rejected: int = 0


def new_run_id() -> str:
    return str(uuid.uuid4())


def start_run(
    conn: snowflake.connector.SnowflakeConnection,
    *,
    pipeline_name: str,
    dataset: str,
    source: str,
    competition_code: str | None = None,
    season: str | None = None,
    matchweek: str | None = None,
) -> RunContext:
    ctx = RunContext(
        run_id=new_run_id(),
        pipeline_name=pipeline_name,
        dataset=dataset,
        source=source,
        competition_code=competition_code,
        season=season,
        matchweek=matchweek,
    )
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO AUDIT.PIPELINE_RUN_AUDIT
                (run_id, pipeline_name, dataset, source, competition_code, season,
                 matchweek, started_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'RUNNING')
            """,
            (
                ctx.run_id,
                ctx.pipeline_name,
                ctx.dataset,
                ctx.source,
                ctx.competition_code,
                ctx.season,
                ctx.matchweek,
                ctx.started_at.isoformat(),
            ),
        )
    finally:
        cursor.close()
    logger.info(
        "pipeline_run_started",
        run_id=ctx.run_id,
        dataset=dataset,
        competition_code=competition_code,
        season=season,
    )
    return ctx


def complete_run(
    conn: snowflake.connector.SnowflakeConnection,
    ctx: RunContext,
    *,
    records_received: int,
    records_inserted: int,
    records_rejected: int = 0,
) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE AUDIT.PIPELINE_RUN_AUDIT
            SET completed_at = %s,
                records_received = %s,
                records_inserted = %s,
                records_rejected = %s,
                status = 'SUCCESS'
            WHERE run_id = %s
            """,
            (
                datetime.now(UTC).isoformat(),
                records_received,
                records_inserted,
                records_rejected,
                ctx.run_id,
            ),
        )
    finally:
        cursor.close()
    logger.info(
        "pipeline_run_succeeded",
        run_id=ctx.run_id,
        records_received=records_received,
        records_inserted=records_inserted,
    )


def fail_run(
    conn: snowflake.connector.SnowflakeConnection, ctx: RunContext, error_message: str
) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE AUDIT.PIPELINE_RUN_AUDIT
            SET completed_at = %s, status = 'FAILED', error_message = %s
            WHERE run_id = %s
            """,
            (datetime.now(UTC).isoformat(), error_message[:4000], ctx.run_id),
        )
    finally:
        cursor.close()
    logger.error("pipeline_run_failed", run_id=ctx.run_id, error=error_message)


def has_successful_run(
    conn: snowflake.connector.SnowflakeConnection,
    *,
    dataset: str,
    competition_code: str,
    season: str,
) -> bool:
    """True if this dataset/competition/season has already been successfully
    ingested. Used to skip re-backfilling immutable, completed historical seasons.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) FROM AUDIT.PIPELINE_RUN_AUDIT
            WHERE dataset = %s AND competition_code = %s AND season = %s
              AND status = 'SUCCESS'
            """,
            (dataset, competition_code, season),
        )
        (count,) = cursor.fetchone()
        return count > 0
    finally:
        cursor.close()
