# ADR-003: Incremental Ingestion Strategy

## Context

Re-downloading every ingested season on every run would waste API calls
(against a 10 req/min budget), waste Snowflake compute, and risk
unnecessary reprocessing of immutable historical data. But the *current*
season's data genuinely changes day to day (fixtures get played, scores
come in, standings shift).

## Options

1. **Always reload everything** - simplest to write, wasteful and slow;
   rejected.
2. **Manual watermarking per dataset with custom logic per entity type** -
   maximally precise, but over-engineered for this project's single-competition,
   single-source scope.
3. **Idempotency via the audit table + a completed-season skip rule** - a
   backfill run checks `AUDIT.PIPELINE_RUN_AUDIT` for an existing `SUCCESS`
   row for that exact `(dataset, competition_code, season)` and skips it
   unless `--force`; the daily job always refreshes the current season only.

## Decision

**Option 3.** See [docs/incremental_strategy.md](../incremental_strategy.md)
for the full mechanics. RAW tables stay append-only (new rows per run, never
updated in place); staging always resolves to "latest load per key," which
is what actually makes reruns safe rather than the skip logic alone.

## Orchestration schedule

A single daily scheduled run (06:00 UTC), not a matchday-frequency poll.
football-data.org's free tier delays live scores and the 10 req/min budget
doesn't support meaningful in-play polling, so a once-daily batch refresh
after matches have settled is both sufficient and the accurate thing to
call this project: "automated daily ingestion," never "real-time."

## Consequences

- Backfill is safe to re-run after a partial failure (e.g. the network
  hiccup that occurred during initial backfill testing) without duplicating
  work or re-spending API budget on already-loaded seasons.
- The daily job's `force=True` behavior means it will happily re-insert
  RAW rows for the current season every day it runs - by design, since
  staging's dedup handles the resulting duplicates and this is the
  simplest way to guarantee the current season never goes stale.
