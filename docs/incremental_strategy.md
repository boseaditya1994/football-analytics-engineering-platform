# Incremental Ingestion Strategy

## Two modes, one code path

```
python -m football_pipeline --mode backfill --start-season 2023 [--force]
python -m football_pipeline --mode daily
```

Both call the same `ingest_competition_season()` function
(`src/football_pipeline/ingestion/ingest_competition_season.py`); only the
orchestration around it differs.

## Backfill

Loops every season from `--start-season` through the current season
(`src/football_pipeline/utils/seasons.py` determines "current" from the
calendar: the Premier League season rolls over in July). For each season,
each of `teams` / `matches` / `standings` is skipped if a `SUCCESS` run
already exists for that exact `(dataset, competition_code, season)` in
`AUDIT.PIPELINE_RUN_AUDIT` - unless `--force` is passed. This is what makes
backfill idempotent: re-running it doesn't re-pull seasons that are already
loaded and complete.

## Daily

Always re-ingests the **current season only**, regardless of prior
successful runs (`force=True` internally) - because a current season's
fixtures, scores, and standings can change day to day. Completed historical
seasons are never touched by the daily job.

## Why this is safe to re-run

RAW tables are append-only: every ingestion run inserts new rows with a
fresh `run_id` and `loaded_at`, rather than updating in place. Staging
models collapse to "latest load per natural key"
(`ROW_NUMBER() ... ORDER BY loaded_at DESC`). Re-running the daily job
twice in one day produces two RAW loads and no double-counting downstream,
since staging always resolves to the most recent one.

## Schedule

The scheduled GitHub Actions run is a single daily job at 06:00 UTC
(`.github/workflows/daily_pipeline.yml`) - not a matchday-frequency poll.
This was a deliberate scope decision (see [ADR-003](adr/ADR-003-incremental-ingestion.md)):
football-data.org's free tier delays live scores, and 10 req/min doesn't
support meaningful in-play polling anyway, so a once-daily batch refresh
after matches have settled is the accurate description of what this
project does - "automated daily ingestion," not "real-time."
