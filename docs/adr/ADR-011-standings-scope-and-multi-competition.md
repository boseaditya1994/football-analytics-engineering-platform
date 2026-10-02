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

## Update: a third and fourth competition proved the generalization

Adding Eredivisie (`DED`) required **zero code or schema changes** - just
running the backfill CLI. `dbt build` passed 85/85 against all three
competitions combined with no new changes, and the dashboard's competition
picker (populated dynamically from `/api/competitions`) picked it up
automatically. This is the real test of whether the grain fix above was a
genuine generalization or a two-competition special case - it generalizes.

Adding Bundesliga (`BL1`) surfaced one more real gap:
`int_match_team_performance` only included `match_status = 'FINISHED'`
matches, silently excluding `AWARDED` matches - forfeits/administrative
decisions with a real, final scoreline, not an in-progress or voided
match. A 2024/25 Bundesliga match between Union Berlin and Bochum was
awarded rather than played to a normal finish; excluding it undercounted
both teams' points and goal difference against the API's own table. Fixed
by including `AWARDED` alongside `FINISHED` in the standings-derivation
input. After the fix, Bochum (credited the win) reconciled perfectly, but
Union Berlin (the forfeiting team) still shows a goal-difference mismatch
- a real, documented pattern where football associations apply a
standardized forfeit goal-difference adjustment to the forfeiting team
that doesn't always equal the literal recorded scoreline. Accepted as a
real-world data limitation, not chased further, since points (the
dimension that actually determines league position) are correctly
resolved. See [docs/reconciliation.md](../reconciliation.md) for full
detail and the real verification numbers across all four competitions.

Adding Ligue 1 (`FL1`) - a fifth competition, again zero schema changes -
generalized the Bundesliga finding further: `AWARDED` matches are the
recurring point where football-data.org's own `/matches` and `/standings`
endpoints disagree with each other, not a one-off. Three separate
instances now (Bundesliga Union Berlin/Bochum; Ligue 1 Montpellier/
Saint-Étienne, where `/standings` doesn't reflect the `/matches`-recorded
result for *either* team; Ligue 1 2025/26 Toulouse, where `/standings`'s
`played_games` hasn't caught up to an `AWARDED` match `/matches` already
shows). This project derives standings from `/matches` for consistency
with every other derived metric; when `/standings` lags behind a specific
`AWARDED` result, reconciliation correctly flags it - there's no way to
know from outside the API which endpoint is more current for a given
contentious match, so this is documented as a recurring upstream
data-consistency characteristic, not chased with speculative timing logic.

## Consequences

- A second competition can be added without re-touching this schema again
  - the grain is now genuinely multi-competition-safe, proven by a third,
    fourth, and fifth competition requiring no further schema changes.
- Reconciliation is stricter and more trustworthy: it caught two real code
  bugs (the join fan-out, and the excluded-AWARDED-matches gap) and
  surfaced a genuine, recurring upstream data-consistency characteristic
  (AWARDED-match endpoint lag) during this change, which is exactly what
  it's for.
- UEFA's full multi-level tie-break, football associations' exact forfeit
  goal-difference conventions, and football-data.org's own endpoint-sync
  lag on AWARDED matches are all explicitly out of scope; documented
  rather than silently wrong or over-engineered to chase edge cases this
  project has no way to resolve from outside the data source.
