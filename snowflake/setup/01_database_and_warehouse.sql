-- ============================================================================
-- Football Analytics Engineering Platform — Database & Warehouse
-- Idempotent: safe to re-run.
-- Run as a role with SYSADMIN privileges (or ACCOUNTADMIN for the first run).
-- ============================================================================

CREATE DATABASE IF NOT EXISTS FOOTBALL_ANALYTICS
    COMMENT = 'Football analytics engineering platform - starts with EPL, designed for multiple leagues/competitions';

-- Smallest practical warehouse, aggressively auto-suspended to control cost.
CREATE WAREHOUSE IF NOT EXISTS FOOTBALL_ANALYTICS_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 1
    COMMENT = 'Single small warehouse for ingestion, dbt builds, and BI queries';
