-- ============================================================================
-- Schemas — RAW / STAGING / INTERMEDIATE / MARTS / AUDIT
-- Single database keeps things simple; schemas separate layers.
-- Multi-league support lives in table design (a COMPETITION dimension),
-- not in separate schemas per league — avoids schema sprawl as leagues are added.
-- ============================================================================

USE DATABASE FOOTBALL_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Untransformed landing zone for data loaded by the Python ingestion pipeline, one table per source entity';

CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT = 'dbt staging models: renamed/typed/cleaned 1:1 views over RAW';

CREATE SCHEMA IF NOT EXISTS INTERMEDIATE
    COMMENT = 'dbt intermediate models: reusable business-logic transformations';

CREATE SCHEMA IF NOT EXISTS MARTS
    COMMENT = 'dbt marts: dimensional model (dims/facts) and BI-facing analytics tables';

CREATE SCHEMA IF NOT EXISTS AUDIT
    COMMENT = 'Pipeline run audit, data quality, and reconciliation tracking tables';
