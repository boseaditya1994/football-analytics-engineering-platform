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

## Authentication: key-pair (required for non-interactive use)

If your account enforces Duo MFA on password logins (common on accounts set
up through Snowflake's free trial with MFA on), password auth will hang or
fail for any non-interactive caller: this dashboard's API, `dbt`, CI, and
the daily-ingestion GitHub Action all need to connect without a human
tapping "approve" on a phone. Key-pair auth solves this - it's Snowflake's
supported method for service/automated access.

1. Generate a key pair (already done once for this project, see
   `.snowflake_keys/` locally - gitignored, never commit the `.p8` private
   key file). To regenerate:
   ```python
   from cryptography.hazmat.primitives import serialization
   from cryptography.hazmat.primitives.asymmetric import rsa
   key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
   # ... see git history of this file for the full script, or ask Claude to redo it
   ```
2. Register the **public** key (not secret) on your Snowflake user - run in
   Snowsight, where you're already authenticated, as `ACCOUNTADMIN`:
   ```sql
   ALTER USER <your_username> SET RSA_PUBLIC_KEY='<public key body, no PEM headers>';
   ```
3. Set `SNOWFLAKE_PRIVATE_KEY_PATH` in `.env` to the private key file's
   path. Leave `SNOWFLAKE_PASSWORD` blank - `connect()` in
   `src/football_pipeline/loaders/snowflake_loader.py` prefers key-pair
   auth whenever `SNOWFLAKE_PRIVATE_KEY_PATH` is set, and only falls back
   to password auth (which will hit MFA) if it's empty.
4. For dbt, `profiles.yml.example` is already configured for
   `authenticator: SNOWFLAKE_JWT` with the same env var.

To rotate the key later (e.g. if it's ever exposed): generate a new pair,
register the new public key with `ALTER USER ... SET RSA_PUBLIC_KEY=...`,
update `.env`, then `ALTER USER ... UNSET RSA_PUBLIC_KEY` to revoke the old
one (or use `RSA_PUBLIC_KEY_2` to overlap during rotation).

## Design notes

- **Single database, layered schemas** (`RAW → STAGING → INTERMEDIATE → MARTS`, plus `AUDIT`) rather than one database per layer — simpler to manage at this scale.
- **Multi-league ready without schema sprawl**: every RAW/fact table carries a `competition_code` column instead of splitting schemas per league. Adding a second competition later (e.g. Championship, La Liga) is a matter of ingesting more rows, not restructuring the warehouse.
- **Cost control**: one XSMALL warehouse, `AUTO_SUSPEND = 60`, `AUTO_RESUME = TRUE`, single cluster. See `docs/adr/ADR-004-snowflake-architecture.md`.
