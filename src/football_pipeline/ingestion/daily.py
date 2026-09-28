"""Daily incremental ingestion: refreshes only the current season's teams,
matches, and standings. Never re-pulls completed historical seasons.
"""

from __future__ import annotations

import snowflake.connector
import structlog

from football_pipeline.api.football_data_client import FootballDataClient
from football_pipeline.ingestion.ingest_competition_season import ingest_competition_season
from football_pipeline.utils.seasons import current_season_start_year

logger = structlog.get_logger(__name__)

PIPELINE_NAME = "football_pipeline.daily"


def run_daily(
    *,
    client: FootballDataClient,
    conn: snowflake.connector.SnowflakeConnection,
    competition_code: str,
) -> dict[str, int]:
    season_start_year = current_season_start_year()
    logger.info(
        "daily_ingestion_start", competition_code=competition_code, season=season_start_year
    )
    # force=True: the current season is never "already loaded and skippable" -
    # it's refreshed every run regardless of prior successful runs.
    return ingest_competition_season(
        client=client,
        conn=conn,
        competition_code=competition_code,
        season_start_year=season_start_year,
        pipeline_name=PIPELINE_NAME,
        force=True,
    )
