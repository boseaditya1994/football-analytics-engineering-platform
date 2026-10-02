{#
    Deterministically derives the league/group-stage table after every
    match a team plays, purely from match results - no reliance on the
    API's own standings endpoint. This is what fact_standing_snapshot is
    built from, and stg_standings (the API's reported table) exists only
    to reconcile against it (see docs/reconciliation.md).

    Scope: only "table" stages are included - REGULAR_SEASON (domestic
    leagues like the Premier League) and LEAGUE_STAGE/GROUP_STAGE (cup
    competitions like the Champions League, both the pre-2024 group format
    and the post-2024 league-phase format). Knockout stages (PLAYOFFS,
    LAST_16, QUARTER_FINALS, SEMI_FINALS, FINAL, ...) have no table/position
    concept - they're elimination ties, not standings - so they're
    excluded here. Those matches still appear in fact_match/fact_team_match
    (match-level analytics works regardless of stage); they just never
    contribute to a league_position. See ADR-011.

    Grain: one row per (competition_code, season, team, match played) -
    every PARTITION BY and the final position RANK() includes
    competition_code so a team's campaigns in two different competitions
    in the same season (e.g. Premier League and Champions League) never
    collide into one aggregated row.

    Algorithm:
    1. Order each team's table-stage matches chronologically by kickoff
       date (not matchweek number - postponements mean they can diverge).
    2. Running totals (played/won/drawn/lost/goals/points) via a window
       SUM(...) OVER (PARTITION BY competition_code, team, season ORDER BY
       kickoff_utc ROWS UNBOUNDED PRECEDING) - i.e. cumulative through and
       including each match.
    3. Position is RANK() partitioned by (competition_code, season,
       matchweek) - the round number carried on the match itself - using
       the standard tie-break: points desc, goal difference desc, goals
       for desc (same order football-data.org's own table uses). Known
       simplification: this assumes every team has played its matchweek-N
       fixture by the time positions are compared, which can be briefly
       untrue around postponed/rearranged matches - acceptable for this
       project's scope, called out here rather than silently glossed over.
#}

with performance as (
    select * from {{ ref('int_match_team_performance') }}
    where match_stage in ('REGULAR_SEASON', 'LEAGUE_STAGE', 'GROUP_STAGE')
),

running_totals as (
    select
        competition_code,
        team_id,
        season,
        match_id,
        matchweek,
        kickoff_utc,
        row_number() over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
        ) as played_games,
        sum(case when result = 'WIN' then 1 else 0 end) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as won,
        sum(case when result = 'DRAW' then 1 else 0 end) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as drawn,
        sum(case when result = 'LOSS' then 1 else 0 end) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as lost,
        sum(goals_for) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as goals_for,
        sum(goals_against) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as goals_against,
        sum(points) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as points
    from performance
)

select
    competition_code,
    team_id,
    season,
    match_id            as as_of_match_id,
    matchweek           as as_of_matchweek,
    kickoff_utc          as as_of_kickoff_utc,
    played_games,
    won,
    drawn,
    lost,
    goals_for,
    goals_against,
    goals_for - goals_against as goal_difference,
    points,
    rank() over (
        partition by competition_code, season, matchweek
        order by points desc, (goals_for - goals_against) desc, goals_for desc
    ) as league_position
from running_totals
