# ADR-005: dbt Materializations & the fact_match / fact_team_match Split

## Context

Two design questions: (1) which dbt materializations to use per layer, and
(2) whether match-level analytics need one fact table or two.

## Materializations

- **Staging**: `view`. Thin rename/type/dedup layer over RAW - re-computing
  it on every query is cheap at this data volume, and a view always
  reflects the latest RAW load with no extra build step.
- **Intermediate**: `view`. Same reasoning; these are reused by multiple
  downstream marts (`int_match_team_performance` feeds both
  `fact_team_match` and `int_table_progression`), so keeping them as views
  avoids storing an extra materialized copy of data that's cheap to
  recompute.
- **Marts**: `table`. These are what the dashboard API queries directly and
  what dbt tests run against - materializing them avoids recomputing the
  full staging→intermediate chain on every dashboard page load.

Incremental materialization (`materialized='incremental'`) was considered
for `fact_match`/`fact_team_match` but not used: at ~1,500 matches across 4
seasons, a full rebuild takes well under a minute. Incremental logic adds
real complexity (merge strategy, `is_incremental()` branching) that isn't
justified at this scale - it would be revisited if a full `dbt build`
started taking minutes instead of seconds, or once genuinely large
multi-league/multi-season volume exists.

## fact_match vs. fact_team_match

**Decision: keep both**, at different grains.

- `fact_match` - one row per match. Natural for match-centric questions
  (final score, total goals in a fixture, venue-neutral analysis) where
  forcing a home/away unpivot would just require re-joining two rows back
  together.
- `fact_team_match` - one row per team per match (home/away normalized).
  Natural for team-centric analytics (points, form, home/away splits,
  rankings) - without it, every team-level query needs a
  `CASE WHEN home_team_id = :team THEN ... ELSE ...`, which is exactly the
  kind of repeated logic `int_match_team_performance` exists to avoid
  (see [docs/data_model.md](../data_model.md)).

## Consequences

- A small amount of storage duplication (goals/results appear in both
  facts) in exchange for every downstream mart being a simple `GROUP BY`
  with no conditional home/away logic repeated per query.
- Adding incremental materialization later is a contained, isolated change
  to two model files - not a redesign - if/when data volume justifies it.
