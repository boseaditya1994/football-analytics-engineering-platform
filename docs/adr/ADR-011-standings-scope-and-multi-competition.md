# ADR-011: Standings Scope and the Multi-Competition Grain Fix

## Context

Adding the Champions League as a second competition surfaced a design gap
that had been explicitly flagged as "revisit when a second competition is
added" in [ADR-006](ADR-006-dimensional-model.md): several models were
keyed by `(team_id, season)` without `competition_code`. football-data.org
reuses the same season string across competitions (a team's `"2023"`
Premier League season and `"2023"` Champions League season are both
literally the string `"2023"`), so without `competition_code` in the grain,
a team playing in both competitions in the same season would have its two
campaigns silently merged into one row.

Champions League data also isn't shaped like a domestic league: matches
split into a league/group stage (which has a table) and knockout rounds
(`LAST_16`, `QUARTER_FINALS`, `SEMI_FINALS`, `FINAL`, etc. - elimination
ties, no table/position concept).

## Decision

**1. `competition_code` added to the grain** of `int_table_progression`,
`fact_standing_snapshot`, `mart_league_table`, `mart_league_progression`,
`mart_team_form`, `mart_home_away_performance`, and `mart_goal_analysis` -
every PARTITION BY, GROUP BY, and uniqueness test. `fact_match` and
`fact_team_match` didn't need the change: their unique key is `match_id`
(or `match_id, team_id`), and `match_id` is globally unique across
competitions in the API already.

**2. Standings derivation scoped to table-eligible stages only**:
`int_table_progression` now filters to `match_stage IN ('REGULAR_SEASON',
'LEAGUE_STAGE', 'GROUP_STAGE')` - domestic league matches, plus both the
pre-2024 Champions League group format and the post-2024 league-phase
format. Knockout-stage matches still appear in `fact_match`/
`fact_team_match` (match-level analytics works regardless of stage); they
just never contribute to a derived `league_position`.

## A real bug this caught

Testing the grain fix against real combined PL+CL data (not just a
synthetic test), the `reconcile.py` script itself turned out to have the
exact bug this ADR exists to prevent: its JOIN from `stg_standings` to
`fact_standing_snapshot` filtered `competition_code` on the source side
only, not in the join condition. Since PL's `"2023"` season and CL's
`"2023"` season share the same string, this fanned out and paired a
team's correct CL standings against its *unrelated* PL row at the same
`(season, matchweek)` - reporting a false mismatch (e.g. Manchester
City's CL goal difference of 11 "mismatching" against its PL goal
difference of 13, a comparison that should never have happened). Fixed
by adding `f.competition_code = s.competition_code` to the join. Verified
by re-running reconciliation for both competitions after the fix.

## A real, accepted limitation this surfaced

After the join fix, one genuine tie-break discrepancy remained: Bayern
Munich and Real Madrid finished the 2024/25 Champions League league phase
level on every criterion this project's tie-break uses (points, goal
difference, goals for) - UEFA's full tie-break order goes further (away
goals, disciplinary points, club coefficient), which this project doesn't
have the data to replicate. `RANK()` assigns both teams the same position;
the API reports them as adjacent, sequentially-ranked positions. This is
documented as an accepted scope boundary, not chased with a deeper
tie-break chain - see [docs/reconciliation.md](../reconciliation.md).
Verified real: 140 teams checked, 420 checks, 16 mismatches, all either
this tie-break case or the already-documented in-progress-season
partial-round comparison (current season, not every team has played the
same number of games yet).

## Consequences

- A second competition can be added without re-touching this schema again
  - the grain is now genuinely multi-competition-safe.
- Reconciliation is stricter and more trustworthy: it caught a real bug in
  itself during this change, which is exactly what it's for.
- UEFA's full multi-level tie-break is explicitly out of scope; documented
  rather than silently wrong or over-engineered to chase a rare edge case.
