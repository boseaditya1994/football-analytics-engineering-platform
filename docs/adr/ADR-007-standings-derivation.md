# ADR-007: Standings Derivation

## Context

football-data.org's `/standings` endpoint returns the *current* table, not
historical per-matchweek snapshots. The project needs a full season's
progression (position/points by matchweek) for the dashboard's title-race
view, and a data-quality showcase feature.

## Options

1. **Store only the API's current-standings snapshot on each daily load**,
   accumulating a history of snapshots over time. Rejected: this only
   builds history going forward from whenever the project starts running
   daily - it can never produce the 2023/24 season's full progression,
   which had already finished before this project existed.
2. **Independently derive the full table, at every matchweek, purely from
   match results.** Deterministic, works retroactively for any season with
   complete match data, and - critically - can be checked against the
   API's own current-table snapshot as a correctness test.

## Decision

**Option 2.** Algorithm implemented in
`dbt_football/models/intermediate/int_table_progression.sql`: cumulative
window functions ordered by kickoff date, ranked within `(season,
matchweek)` using the standard points/GD/GF tie-break. Full detail in
[docs/data_model.md](../data_model.md#standings-derivation-algorithm).

This is also what makes [reconciliation](../reconciliation.md) possible at
all - the project can only detect drift between "what the API says the
final table is" and "what we computed" because the two are produced by
genuinely independent paths, not because one is copied from the other with
a checksum.

## Consequences

- Full retroactive progression for every backfilled season, not just ones
  captured going forward.
- A real, provable data-quality feature: 840 checks run, 0 mismatches
  against the API's own reported standings, across all 4 ingested seasons.
- The known simplification around postponed matches (documented in
  [docs/data_model.md](../data_model.md)) is a direct consequence of using
  matchweek-number ranking rather than exact calendar-time ranking, which
  was tried first and found to be wrong (teams play at staggered times
  within the same round, so exact-timestamp ranking compared teams that
  hadn't actually reached the same point in the season).
