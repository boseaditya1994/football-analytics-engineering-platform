.PHONY: setup backfill ingest dbt-build dbt-test reconcile test lint pipeline

setup:
	python -m venv .venv
	.venv/Scripts/pip install -e ".[dev]"

backfill:
	python -m football_pipeline --mode backfill --start-season $(START_SEASON)

ingest:
	python -m football_pipeline --mode daily

dbt-build:
	cd dbt_football && dbt build

dbt-test:
	cd dbt_football && dbt test

reconcile:
	python -m football_pipeline.audit.reconcile

test:
	pytest

lint:
	ruff check src tests

pipeline: ingest dbt-build reconcile
