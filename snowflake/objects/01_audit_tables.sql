-- ============================================================================
-- AUDIT schema tables — pipeline observability, data quality, reconciliation.
-- These are written to directly by the Python pipeline (not managed by dbt),
-- since they need to exist before any dbt run and track raw ingestion runs.
-- ============================================================================

USE DATABASE FOOTBALL_ANALYTICS;
USE SCHEMA AUDIT;

CREATE TABLE IF NOT EXISTS PIPELINE_RUN_AUDIT (
    run_id            STRING         NOT NULL,
    pipeline_name     STRING         NOT NULL,  -- e.g. 'football_pipeline.backfill', 'football_pipeline.daily'
    dataset           STRING         NOT NULL,  -- e.g. 'matches', 'teams', 'standings'
    source            STRING         NOT NULL,  -- e.g. 'football-data.org'
    competition_code  STRING,                   -- e.g. 'PL' — multi-league ready
    season            STRING,
    matchweek         STRING,
    watermark         TIMESTAMP_NTZ,
    started_at        TIMESTAMP_NTZ  NOT NULL,
    completed_at      TIMESTAMP_NTZ,
    records_received  NUMBER,
    records_inserted  NUMBER,
    records_updated   NUMBER,
    records_rejected  NUMBER,
    status            STRING         NOT NULL,  -- RUNNING | SUCCESS | FAILED
    error_message     STRING,
    PRIMARY KEY (run_id)
)
COMMENT = 'One row per ingestion run per dataset — observability for the Python pipeline';

CREATE TABLE IF NOT EXISTS DATA_QUALITY_AUDIT (
    check_id           STRING         NOT NULL,
    run_id             STRING,
    dbt_invocation_id  STRING,
    model_name         STRING         NOT NULL,
    test_name          STRING         NOT NULL,
    status             STRING         NOT NULL,  -- PASS | FAIL | WARN
    failing_row_count  NUMBER,
    executed_at        TIMESTAMP_NTZ  NOT NULL,
    PRIMARY KEY (check_id)
)
COMMENT = 'Record of dbt test outcomes over time, for trend/health reporting';

CREATE TABLE IF NOT EXISTS RECONCILIATION_AUDIT (
    reconciliation_id  STRING         NOT NULL,
    run_id             STRING,
    competition_code   STRING,
    season             STRING,
    check_name         STRING         NOT NULL,  -- e.g. 'standings_position_match'
    entity_key         STRING,                   -- e.g. team code / match id
    source_value       VARIANT,
    derived_value      VARIANT,
    is_match           BOOLEAN        NOT NULL,
    executed_at        TIMESTAMP_NTZ  NOT NULL,
    PRIMARY KEY (reconciliation_id)
)
COMMENT = 'API-reported vs. independently-derived value comparisons (e.g. league standings)';
