"""CLI entrypoint.

Usage:
    python -m football_pipeline --mode backfill --start-season 2018 [--competition PL] [--force]
    python -m football_pipeline --mode daily [--competition PL]
"""

from __future__ import annotations

import argparse
import sys

import structlog

from football_pipeline.api.football_data_client import FootballDataClient
from football_pipeline.config.settings import get_settings
from football_pipeline.ingestion import run_backfill, run_daily
from football_pipeline.loaders.snowflake_loader import connect
from football_pipeline.utils.logging import configure_logging

logger = structlog.get_logger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="football_pipeline")
    parser.add_argument("--mode", choices=["backfill", "daily"], required=True)
    parser.add_argument(
        "--competition", default="PL", help="football-data.org competition code (default: PL)"
    )
    parser.add_argument(
        "--start-season", type=int, help="Season start year to backfill from, e.g. 2018"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest seasons even if a successful run is already recorded",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)

    if args.mode == "backfill" and args.start_season is None:
        logger.error("missing_start_season", message="--start-season is required for --mode backfill")
        return 2

    conn = connect(settings)
    try:
        with FootballDataClient(
            api_key=settings.football_data_api_key, base_url=settings.football_data_base_url
        ) as client:
            if args.mode == "backfill":
                results = run_backfill(
                    client=client,
                    conn=conn,
                    competition_code=args.competition,
                    start_season=args.start_season,
                    force=args.force,
                )
            else:
                results = run_daily(client=client, conn=conn, competition_code=args.competition)
    finally:
        conn.close()

    logger.info("pipeline_run_complete", mode=args.mode, results=results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
