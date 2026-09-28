"""Historical backfill: ingest every season from start_season through the
current season for a competition.
"""

from __future__ import annotations

import snowflake.connector
import structlog

from football_pipeline.api.football_data_client import FootballDataClient
from football_pipeline.ingestion.ingest_competition_season import (
    ingest_competition_metadata,
    ingest_competition_season,
)
from football_pipeline.utils.seasons import season_range

logger = structlog.get_logger(__name__)

PIPELINE_NAME = "football_pipeline.backfill"


def run_backfill(
    *,
    client: FootballDataClient,
    conn: snowflake.connector.SnowflakeConnection,
    competition_code: str,
    start_season: int,
    force: bool = False,
) -> dict[int, dict[str, int]]:
    ingest_competition_metadata(
        client=client, conn=conn, competition_code=competition_code, pipeline_name=PIPELINE_NAME
    )

    results: dict[int, dict[str, int]] = {}
    for season_start_year in season_range(start_season):
        logger.info(
            "backfill_season_start", competition_code=competition_code, season=season_start_year
        )
        results[season_start_year] = ingest_competition_season(
            client=client,
            conn=conn,
            competition_code=competition_code,
            season_start_year=season_start_year,
            pipeline_name=PIPELINE_NAME,
            force=force,
        )
    return results
