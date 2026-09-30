# Metric Definitions

Every metric shown in the dashboard or computed in a mart, defined exactly
as implemented - no metric here is approximate or "close enough."

| Metric | Definition | Source model |
|---|---|---|
| **Points** | 3 for a win, 1 for a draw, 0 for a loss | `int_match_team_performance.points` |
| **Points Per Game (PPG)** | `points / played_games` | `mart_league_table.points_per_game` |
| **Goal Difference (GD)** | `goals_for - goals_against` | `fact_team_match.goal_difference` |
| **League Position** | `RANK()` within `(season, matchweek)`, ordered by points desc, then goal difference desc, then goals for desc | `int_table_progression.league_position` |
| **Win %** | `wins / played_games * 100` | `mart_home_away_performance.home_win_pct` / `away_win_pct` |
| **Clean Sheet %** | `(matches with goals_against = 0) / played_games * 100` | `mart_goal_analysis.clean_sheet_pct` |
| **Failed to Score %** | `(matches with goals_for = 0) / played_games * 100` | `mart_goal_analysis.failed_to_score_pct` |
| **Home/Away PPG** | Points Per Game, computed separately over only a team's home fixtures or only its away fixtures | `mart_home_away_performance` |
| **Form (last 5 / last 10)** | The sequence of `WIN`/`DRAW`/`LOSS` results over a team's most recent 5 or 10 matches (by kickoff date), plus rolling PPG/goals over that window | `mart_team_form` |
| **Position Change** | `previous_matchweek_position - league_position` (positive = moved up the table) | `mart_league_progression.position_change` |

## Deliberately not implemented

- **Expected Goals (xG)**: no free, continuous, multi-season xG source exists
  for the seasons this project covers (see [docs/data_sources.md](data_sources.md)).
  Never approximated with a simplistic formula and mislabeled as xG.
- **Points recovered from a losing position / dropped from a winning
  position**: requires in-match timeline/event data (when a team went
  behind, and the eventual result), which football-data.org's free tier
  does not provide. Not derivable from final scores alone, and not
  approximated.
- **Shots-based metrics (conversion rate, shots on target %)**: no shot
  data available on the free tier.

## Denominators

Every percentage above is computed against `played_games` for the scope in
question (e.g. home win % divides by home games played, not total games
played) - never against total matches in the season, which would understate
the metric for a team that hasn't played all its fixtures yet.
