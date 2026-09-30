# ADR-009: Orchestration & Snowflake Authentication

## Context

The pipeline needs to run non-interactively: a GitHub Actions scheduled
job, and the dashboard's FastAPI backend. Both need a Snowflake connection
with nobody available to approve an interactive prompt.

## What actually happened

Building the dashboard API's `/pipeline-health` endpoint, requests started
hanging indefinitely and eventually failing. The real error, once
surfaced, was:

```
snowflake.connector.errors.DatabaseError: ... Duo Security authentication is denied.
```

This Snowflake account enforces Duo MFA on password logins. Every prior
intermittent "could not connect to Snowflake backend" error earlier in the
project's development was very likely the same root cause - a Duo push
notification timing out with nobody there to approve it. Password auth
fundamentally cannot work for a non-interactive caller on this account.

## Decision

**Key-pair authentication** (Snowflake's supported mechanism for
service/automated access), not password auth, for every non-interactive
caller:

- `src/football_pipeline/loaders/snowflake_loader.py`'s `connect()`
  prefers `SNOWFLAKE_PRIVATE_KEY_PATH` when set, falling back to password
  only for interactive local use.
- `dbt_football/profiles.yml.example` uses `authenticator: SNOWFLAKE_JWT`.
- `.github/workflows/daily_pipeline.yml` writes the private key from a
  GitHub Actions secret (`SNOWFLAKE_PRIVATE_KEY`) to a temp file for the
  run's duration, removed afterward regardless of outcome.

The public key (not sensitive by design) is registered on the Snowflake
user via `ALTER USER ... SET RSA_PUBLIC_KEY = ...`, run once manually in
Snowsight - see `snowflake/README.md`.

**Orchestration**: a single GitHub Actions scheduled workflow
(`cron: "0 6 * * *"`) plus `workflow_dispatch` for manual runs. No separate
orchestrator (Airflow/Dagster/Prefect) - unjustified for a single daily job
with three sequential steps (ingest → dbt build → reconcile) and no
branching/backfill-on-demand requirement beyond what the CLI's
`--mode backfill` already provides locally.

## Consequences

- CI and the dashboard API both connect with zero MFA prompts, verified
  end-to-end in a real GitHub Actions run (ingestion → dbt build →
  reconciliation, all green, real data loaded).
- The private key file is gitignored (`.snowflake_keys/`, `*.p8`) and never
  committed; only the public key (not secret) was ever shared to register
  it.
- If the key is ever exposed, rotation is a contained operation: generate a
  new pair, register the new public key, update the secret/`.env`, then
  `ALTER USER ... UNSET RSA_PUBLIC_KEY` on the old one.
