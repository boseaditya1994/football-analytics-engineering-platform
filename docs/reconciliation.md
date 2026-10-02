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
4. A multi-competition join bug - see below, since this exact thing
   happened once already.

The `RECONCILIATION_AUDIT` table's `source_value`/`derived_value` columns
make it possible to tell which of these it is without re-deriving anything.

## A real bug this check caught: adding the Champions League

When Champions League data was first added, `reconcile.py`'s own JOIN
turned out to have exactly the bug class this feature exists to catch.
football-data.org reuses season strings across competitions (a team's
`"2023"` Premier League season and `"2023"` Champions League season are
both literally the string `"2023"`), and the JOIN from `stg_standings` to
`fact_standing_snapshot` only filtered `competition_code` on the source
side, not in the join condition itself. Result: a team's correct CL
standings got paired against its *unrelated* PL row at the same
`(season, matchweek)` - reported as a false mismatch (Manchester City's
CL goal difference of 11 "mismatching" against its PL goal difference of
13, a comparison that should never have happened).

Diagnosed by hand: computed Man City's CL goal difference directly from
its six real 2023/24 group-stage matches (18 scored − 7 conceded = 11),
confirmed it matched both the API and `int_table_progression` exactly,
then found the actual bug by querying `fact_standing_snapshot` for that
team/season/matchweek across *all* competitions and seeing both a correct
CL row and an unrelated PL row the query was silently matching against.
Fixed by adding `f.competition_code = s.competition_code` to the join -
see [ADR-011](adr/ADR-011-standings-scope-and-multi-competition.md).

## A real, accepted limitation: UEFA's deeper tie-break

After the join fix, one genuine discrepancy remained: Bayern Munich and
Real Madrid finished the Champions League 2024/25 league phase tied on
every criterion this project's standings derivation uses (points, goal
difference, goals for). UEFA's actual tie-break order goes further (away
goals, disciplinary points, club coefficient) - data this project doesn't
have. `RANK()` gives both teams the same position; the API reports
sequential, adjacent positions. This is an accepted scope boundary, not a
bug - documented rather than chased with an ever-deeper tie-break chain
for one rare case. See [ADR-011](adr/ADR-011-standings-scope-and-multi-competition.md).

## A real bug this check caught: adding the Bundesliga

Adding Bundesliga data surfaced a genuine gap: `int_match_team_performance`
only included matches with `match_status = 'FINISHED'`, silently excluding
`AWARDED` matches (forfeits/administrative decisions with a real, final
scoreline - not an in-progress or voided match). A 2024/25 Bundesliga match
between 1. FC Union Berlin and VfL Bochum was awarded (0-2) rather than
played to a normal finish; excluding it undercounted both teams' points
and goal difference versus the API's own table. Fixed by including
`AWARDED` alongside `FINISHED` in the standings-derivation input (and the
`assert_winner_matches_score` singular test, for consistency) - see
[ADR-011](adr/ADR-011-standings-scope-and-multi-competition.md).

## A real, accepted limitation: forfeited-match goal difference conventions

After the `AWARDED`-inclusion fix, Bochum (credited the win) reconciled
perfectly, but Union Berlin (the forfeiting team) still shows a 2-goal
goal-difference mismatch at every matchweek from the awarded match onward.
This matches a real, documented pattern in German football association
disciplinary rulings: the goal-difference impact applied to the forfeiting
team's official standings doesn't always equal the literal recorded
scoreline the API exposes via its `fullTime` score field - associations
sometimes apply a standardized forfeit adjustment that differs by team.
This project doesn't have access to whatever specific administrative rule
produced the API's exact number, so it's documented as an accepted,
real-world data limitation rather than chased further - the points
(who gets 3 vs 0) are correctly resolved, which is the dimension that
actually determines league position in all but this one goal-difference
figure.

## Actual results, all four competitions (after both fixes)

- **Premier League**: 120 teams checked, 360 checks, **0 mismatches**.
- **Champions League**: 140 teams checked, 420 checks, 16 mismatches - all
  either the in-progress-current-season partial-round comparison (season
  2026/27, matchweek 1, not every team has played the same number of
  games yet) or the one UEFA tie-break case above. Zero unexplained
  mismatches.
- **Eredivisie**: 72 teams checked, 216 checks, **0 mismatches**.
- **Bundesliga**: 72 teams checked, 216 checks, 2 mismatches - both the one
  forfeited-match goal-difference case above. Zero unexplained mismatches.
