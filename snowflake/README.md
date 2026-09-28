# Snowflake Setup

All Snowflake objects are version-controlled SQL, run in this order:

1. `setup/01_database_and_warehouse.sql` — creates `FOOTBALL_ANALYTICS` database and `FOOTBALL_ANALYTICS_WH` warehouse (XSMALL, auto-suspend 60s). Run as `SYSADMIN` (or `ACCOUNTADMIN`).
2. `setup/02_schemas.sql` — creates `RAW`, `STAGING`, `INTERMEDIATE`, `MARTS`, `AUDIT` schemas.
3. `setup/03_roles_and_grants.sql` — creates `FOOTBALL_ANALYTICS_ROLE` and grants it usage/DDL/DML on the database. Run as `ACCOUNTADMIN`. **Edit the final `GRANT ROLE ... TO USER ...` line with your actual username before running it**, or run that one line manually.
4. `objects/01_audit_tables.sql` — `AUDIT` schema tables (`PIPELINE_RUN_AUDIT`, `DATA_QUALITY_AUDIT`, `RECONCILIATION_AUDIT`) written to directly by the Python pipeline.
5. `objects/02_raw_tables.sql` — `RAW` schema landing tables (VARIANT payload + load metadata), one per source entity.

## Two ways to run these

**Option A — Snowsight (manual, no credentials needed from you in this session):**
Paste each file's contents into a Snowsight worksheet and run, in the order above.

**Option B — scripted, via your own `.env`:**
1. Copy `.env.example` to `.env` in the project root and fill in your Snowflake account, user, password (or key-pair), and role — you edit this file yourself, it's never sent through chat and is gitignored.
2. Run `python snowflake/run_setup.py`. It reads `.env`, connects, and executes each file above in order. It only prints object names and statuses — never credential values.

## Design notes

- **Single database, layered schemas** (`RAW → STAGING → INTERMEDIATE → MARTS`, plus `AUDIT`) rather than one database per layer — simpler to manage at this scale.
- **Multi-league ready without schema sprawl**: every RAW/fact table carries a `competition_code` column instead of splitting schemas per league. Adding a second competition later (e.g. Championship, La Liga) is a matter of ingesting more rows, not restructuring the warehouse.
- **Cost control**: one XSMALL warehouse, `AUTO_SUSPEND = 60`, `AUTO_RESUME = TRUE`, single cluster. See `docs/adr/ADR-004-snowflake-architecture.md`.
