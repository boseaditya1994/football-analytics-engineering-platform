# Reconciliation

## Why this exists

Most portfolio data projects test data quality with `not_null`/`unique`
checks and call it done. Those catch malformed rows, but they don't catch
**a transformation that's confidently wrong** - a bug in the business logic
that produces well-formed, plausible-looking, incorrect numbers. This
project's standings are the highest-stakes derived metric it produces
(everything else - form, home/away splits, goal analysis - is a simpler
aggregation), so it gets an actual second opinion, not just a shape check.

## What's compared

`fact_standing_snapshot` (this project's own standings, derived purely from
match results - see [docs/data_model.md](data_model.md#standings-derivation-algorithm))
against `stg_standings` (football-data.org's own reported table for that
team, staged as-is). Implemented in
`src/football_pipeline/audit/reconcile.py`, run as part of the scheduled
pipeline (`.github/workflows/daily_pipeline.yml`) after every `dbt build`.

Three checks per team per season:

| Check | API value | Derived value |
|---|---|---|
| `standings_position` | `stg_standings.api_position` | `fact_standing_snapshot.league_position` |
| `standings_points` | `stg_standings.points` | `fact_standing_snapshot.points` |
| `standings_goal_difference` | `stg_standings.goal_difference` | `fact_standing_snapshot.goal_difference` |

**Join key note**: the API's standings response is a snapshot of the
*current* table - it carries `played_games`, not a matchweek number. A
team's `played_games` count IS the matchweek it has completed, so that's
the correct join key into `fact_standing_snapshot.matchweek` (this was
originally written assuming a `matchweek` column existed on the API side;
it doesn't, and the first real run caught that immediately - see the
`ci: automate EPL daily pipeline` commit).

## Where results go

Every check's outcome (source value, derived value, match/no-match) is
written to `AUDIT.RECONCILIATION_AUDIT`. The pipeline **fails loudly** -
non-zero exit code - if any mismatch is found, rather than logging a
warning and continuing.

## Actual results

As of this writing: **840 checks run, 0 mismatches**, across all 4 ingested
seasons (2023/24-2026/27) x 20-27 teams x 3 checks. Verified independently
by hand during development (not just by trusting the automated check):

```
Man City FC   2023/24: API position 1, derived position 1, points 91=91
Arsenal FC    2023/24: API position 2, derived position 2, points 89=89
```

matching real, known Premier League history (Manchester City won the
2023/24 title with 91 points; Arsenal finished second with 89).

## What a real mismatch would mean

If this check ever fails, it means one of:
1. The standings-derivation algorithm has a bug (tie-break order, a
   miscounted match, a double-counted result).
2. The API's own data changed in a way our derivation hasn't caught up
   with yet (e.g. a match result correction, an awarded/expunged result).
3. A postponement broke the "every team has played its matchweek-N fixture"
   assumption noted in [docs/data_model.md](data_model.md#standings-derivation-algorithm).

The `RECONCILIATION_AUDIT` table's `source_value`/`derived_value` columns
make it possible to tell which of these it is without re-deriving anything.
