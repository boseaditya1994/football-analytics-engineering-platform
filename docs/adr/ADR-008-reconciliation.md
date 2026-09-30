# ADR-008: Reconciliation Strategy

## Context

`not_null`/`unique`/`relationships` dbt tests catch malformed data, but
not a confidently-wrong transformation - the standings-derivation logic
([ADR-007](ADR-007-standings-derivation.md)) could have a subtle bug (a
tie-break ordering mistake, a double-counted result) and still produce
well-formed, plausible rows that pass every schema test.

## Decision

Compare the independently-derived `fact_standing_snapshot` against the
API's own reported `stg_standings`, per team per season, on three
dimensions: league position, points, goal difference. Implemented in
`src/football_pipeline/audit/reconcile.py`, run as a pipeline step after
every `dbt build` (`.github/workflows/daily_pipeline.yml`), writing every
check's outcome - match or mismatch, both values - to
`AUDIT.RECONCILIATION_AUDIT`. The pipeline exits non-zero on any mismatch,
so CI fails loudly rather than a silent data-quality regression shipping
to the dashboard.

Full detail, including the real join-key bug this surfaced on first run
(the API's standings response has no `matchweek` column, only
`played_games`), is in [docs/reconciliation.md](../reconciliation.md).

## Consequences

- A genuine second opinion on the highest-stakes derived metric in the
  project, not just a shape check.
- `RECONCILIATION_AUDIT`'s `source_value`/`derived_value` columns make a
  future mismatch diagnosable without re-deriving anything by hand.
- This pattern (derive independently, then reconcile against source) is
  the template for any future derived metric this project adds that has a
  source-of-truth to check against.
