# Football Analytics Engineering Platform

> Status: **early build** — repository bootstrap complete, ingestion/dbt/Snowflake build-out in progress.

An end-to-end analytics engineering platform that ingests, models, tests, and
serves football competition data — starting with the English Premier League,
architected to extend to additional leagues and competitions over time.

## Tech Stack

Python · Snowflake · dbt (Fusion) · SQL · React · GitHub Actions

## Project Structure

- `src/football_pipeline/` — Python ingestion framework (API clients, loaders, audit)
- `dbt_football/` — dbt project: staging → intermediate → dimensional marts
- `snowflake/` — version-controlled Snowflake DDL (database, schemas, roles, warehouses)
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

## Disclaimer

This is an independent portfolio/educational analytics engineering project
and is not affiliated with, endorsed by, or sponsored by the Premier League,
any other football competition, or their clubs. Data attribution and usage
are subject to the terms of the selected data provider(s).
