"""Ingests one competition + one season: teams, matches, standings.

Idempotency: a completed historical season is only re-ingested if `force`
is set. The current (in-progress) season is always refreshed, since its
fixtures/results/standings can still change.
"""

from __future__ import annotations

import snowflake.connector
import structlog

from football_pipeline.api.football_data_client import FootballDataClient
from football_pipeline.audit import run_audit
from football_pipeline.loaders.snowflake_loader import SnowflakeLoader
from football_pipeline.utils.seasons import is_current_season

logger = structlog.get_logger(__name__)

SOURCE = "football-data.org"


def ingest_competition_metadata(
    *,
    client: FootballDataClient,
    conn: snowflake.connector.SnowflakeConnection,
    competition_code: str,
    pipeline_name: str,
) -> int:
    """Loads competition-level metadata (name, area, current season). Cheap
    single-record call - always refreshed rather than skipped.
    """
    loader = SnowflakeLoader(conn)
    ctx = run_audit.start_run(
        conn,
        pipeline_name=pipeline_name,
        dataset="competitions",
        source=SOURCE,
        competition_code=competition_code,
    )
    try:
        payload = client.get_competition(competition_code)
        record_count = loader.load_competition(
            competition_code=competition_code,
            run_id=ctx.run_id,
            source=SOURCE,
            payload=payload,
        )
        run_audit.complete_run(
            conn, ctx, records_received=record_count, records_inserted=record_count
        )
        return record_count
    except Exception as exc:
        run_audit.fail_run(conn, ctx, error_message=str(exc))
        raise


def ingest_competition_season(
    *,
    client: FootballDataClient,
    conn: snowflake.connector.SnowflakeConnection,
    competition_code: str,
    season_start_year: int,
    pipeline_name: str,
    force: bool = False,
) -> dict[str, int]:
    season = str(season_start_year)
    loader = SnowflakeLoader(conn)
    results: dict[str, int] = {}

    for dataset, ingest_fn in (
        ("teams", _ingest_teams),
        ("matches", _ingest_matches),
        ("standings", _ingest_standings),
    ):
        if (
            not is_current_season(season_start_year)
            and not force
            and run_audit.has_successful_run(
                conn, dataset=dataset, competition_code=competition_code, season=season
            )
        ):
            logger.info(
                "ingestion_skipped_already_loaded",
                dataset=dataset,
                competition_code=competition_code,
                season=season,
            )
            results[dataset] = 0
            continue

        ctx = run_audit.start_run(
            conn,
            pipeline_name=pipeline_name,
            dataset=dataset,
            source=SOURCE,
            competition_code=competition_code,
            season=season,
        )
        try:
            record_count = ingest_fn(client, loader, competition_code, season, ctx.run_id)
            run_audit.complete_run(
                conn, ctx, records_received=record_count, records_inserted=record_count
            )
            results[dataset] = record_count
        except Exception as exc:
            run_audit.fail_run(conn, ctx, error_message=str(exc))
            raise

    return results


def _ingest_teams(
    client: FootballDataClient,
    loader: SnowflakeLoader,
    competition_code: str,
    season: str,
    run_id: str,
) -> int:
    teams = client.get_teams(competition_code, season=season)
    return loader.load_teams(
        competition_code=competition_code,
        season=season,
        run_id=run_id,
        source=SOURCE,
        teams=teams,
    )


def _ingest_matches(
    client: FootballDataClient,
    loader: SnowflakeLoader,
    competition_code: str,
    season: str,
    run_id: str,
) -> int:
    matches = client.get_matches(competition_code, season=season)
    return loader.load_matches(
        competition_code=competition_code,
        season=season,
        run_id=run_id,
        source=SOURCE,
        matches=matches,
    )


def _ingest_standings(
    client: FootballDataClient,
    loader: SnowflakeLoader,
    competition_code: str,
    season: str,
    run_id: str,
) -> int:
    standings = client.get_standings(competition_code, season=season)
    return loader.load_standings(
        competition_code=competition_code,
        season=season,
        run_id=run_id,
        source=SOURCE,
        payload=standings,
    )
