# Football Analytics Engineering Platform

> Status: **core platform functional** — ingestion, Snowflake, dbt (staging → intermediate → marts), reconciliation, React dashboard, and CI/CD are all built and verified against real data.

An end-to-end analytics engineering platform that ingests, models, tests, and
serves football competition data — starting with the English Premier League,
architected to extend to additional leagues and competitions over time.

## Tech Stack

Python · Snowflake · dbt (Fusion) · SQL · React · GitHub Actions

## Project Structure

- `src/football_pipeline/` — Python ingestion framework (API clients, loaders, audit)
- `dbt_football/` — dbt project: staging → intermediate → dimensional marts
- `snowflake/` — version-controlled Snowflake DDL (database, schemas, roles, warehouses)
- `dashboards/api/` — read-only FastAPI backend over the Snowflake marts
- `dashboards/react/` — React analytics dashboard
- `docs/` — architecture, data sources, data model, ADRs
- `.github/workflows/` — CI and scheduled pipeline automation

## Current Scope (MVP)

Primary data source: [football-data.org](https://www.football-data.org/) (free tier).
Competition scope starts with the **English Premier League**; the schema and
pipeline are designed so additional competitions can be added without a
redesign (see [docs/data_sources.md](docs/data_sources.md) and
[docs/architecture.md](docs/architecture.md), added as the build progresses).

## Setup

See `Makefile` for local developer commands (`make setup`, `make backfill`,
`make ingest`, `make dbt-build`, `make dbt-test`, `make pipeline`).

Copy `.env.example` to `.env` and fill in your own football-data.org API key
and Snowflake credentials — never commit `.env`.

## CI/CD & Automation

- **`.github/workflows/ci.yml`** — runs on every push/PR: `ruff` lint,
  `pytest` (all Snowflake calls mocked, no live connection needed), and
  `dbt parse` against a throwaway dummy profile to catch Jinja/YAML/SQL
  structural errors without touching a real warehouse.
- **`.github/workflows/daily_pipeline.yml`** — scheduled daily (06:00 UTC)
  plus manual trigger: runs `--mode daily` ingestion, `dbt build`, then the
  standings reconciliation check (`football_pipeline.audit.reconcile`),
  which fails the run if our independently-derived standings ever disagree
  with the API's own reported table.

Both workflows authenticate to Snowflake via **key-pair auth**, not a
password — this account enforces Duo MFA on password logins, which would
otherwise block any non-interactive CI run waiting on a phone approval that
never comes. See `snowflake/README.md` for how the key pair is set up.

Required repository secrets: `FOOTBALL_DATA_API_KEY`, `SNOWFLAKE_ACCOUNT`,
`SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY` (the private key file's contents).

## Disclaimer

This is an independent portfolio/educational analytics engineering project
and is not affiliated with, endorsed by, or sponsored by the Premier League,
any other football competition, or their clubs. Data attribution and usage
are subject to the terms of the selected data provider(s).
