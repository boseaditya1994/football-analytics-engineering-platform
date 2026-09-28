# ADR-004: Snowflake Architecture

## Context

The platform needs a warehouse layer that supports layered ELT (raw →
staging → intermediate → marts), is cheap to run at portfolio scale, and
won't need restructuring when more leagues/competitions are added later
(per the project's stated long-term direction).

## Options

1. **One database per layer** (`RAW_DB`, `STAGING_DB`, `MARTS_DB`, ...) — clean
   isolation, but more objects to manage and more cross-database grants for a
   single-developer project.
2. **One database, one schema per layer** (`FOOTBALL_ANALYTICS.RAW`, `.STAGING`,
   `.INTERMEDIATE`, `.MARTS`, `.AUDIT`) — standard dbt-friendly layout, simpler
   grants, still gives clean separation via schema boundaries.
3. **Schema-per-competition** (e.g. `RAW_EPL`, `RAW_LALIGA`) to prepare for
   multi-league — rejected: multiplies schema count for every league added
   and pushes cross-league analytics (e.g. comparing PL vs. Championship) into
   cross-schema joins instead of a `WHERE competition_code = ...` filter.

## Decision

Use **option 2**: single database `FOOTBALL_ANALYTICS`, five schemas
(`RAW`, `STAGING`, `INTERMEDIATE`, `MARTS`, `AUDIT`). Multi-league readiness
is handled at the **column level** — every RAW and fact table carries a
`competition_code` — not at the schema level. One `FOOTBALL_ANALYTICS_WH`
warehouse (XSMALL, single cluster, `AUTO_SUSPEND=60`, `AUTO_RESUME=TRUE`)
serves ingestion, dbt builds, and BI queries; this is a portfolio project
with low, spiky query volume, so a second warehouse isn't justified yet.

## Consequences

- Adding a new league/competition later requires no DDL changes to the
  Snowflake layer — only new rows with a different `competition_code`, and
  dbt models that already group/filter by it.
- All roles and grants are scoped to a single database, keeping
  `03_roles_and_grants.sql` simple.
- If query concurrency or cost ever becomes a real constraint (unlikely at
  this scale), splitting BI traffic onto a second warehouse is a later,
  isolated change — not a redesign.
