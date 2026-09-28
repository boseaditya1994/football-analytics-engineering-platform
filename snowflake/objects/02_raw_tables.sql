-- ============================================================================
-- RAW schema — landing tables for football-data.org entities.
-- Pattern: store the raw API payload as VARIANT + a handful of load metadata
-- columns. dbt staging models are responsible for flattening/typing — RAW
-- stays a faithful, replayable copy of what the API returned.
--
-- competition_code is included on every table so additional leagues can be
-- ingested later without any schema change here.
-- ============================================================================

USE DATABASE FOOTBALL_ANALYTICS;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS RAW_COMPETITIONS (
    competition_code  STRING         NOT NULL,
    run_id            STRING         NOT NULL,
    source            STRING         NOT NULL,
    loaded_at         TIMESTAMP_NTZ  NOT NULL,
    raw_json          VARIANT        NOT NULL
)
COMMENT = 'Raw competition/league metadata payloads, one row per load';

CREATE TABLE IF NOT EXISTS RAW_TEAMS (
    competition_code  STRING         NOT NULL,
    season            STRING,
    run_id            STRING         NOT NULL,
    source            STRING         NOT NULL,
    loaded_at         TIMESTAMP_NTZ  NOT NULL,
    raw_json          VARIANT        NOT NULL
)
COMMENT = 'Raw team metadata payloads, one row per team per load';

CREATE TABLE IF NOT EXISTS RAW_MATCHES (
    competition_code  STRING         NOT NULL,
    season            STRING         NOT NULL,
    matchweek         STRING,
    match_id          STRING         NOT NULL,
    run_id            STRING         NOT NULL,
    source            STRING         NOT NULL,
    loaded_at         TIMESTAMP_NTZ  NOT NULL,
    raw_json          VARIANT        NOT NULL
)
COMMENT = 'Raw match payloads (fixture, status, score), one row per match per load';

CREATE TABLE IF NOT EXISTS RAW_STANDINGS (
    competition_code  STRING         NOT NULL,
    season            STRING         NOT NULL,
    snapshot_date     DATE           NOT NULL,
    run_id            STRING         NOT NULL,
    source            STRING         NOT NULL,
    loaded_at         TIMESTAMP_NTZ  NOT NULL,
    raw_json          VARIANT        NOT NULL
)
COMMENT = 'Raw API-reported standings table payloads, one row per snapshot load';
