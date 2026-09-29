{#
    Deterministically derives the league table after every match a team
    plays, purely from match results - no reliance on the API's own
    standings endpoint. This is what fact_standing_snapshot is built from,
    and stg_standings (the API's reported table) exists only to reconcile
    against it (see docs/reconciliation.md).

    Algorithm:
    1. Order each team's matches chronologically by kickoff date (not
       matchweek number - postponements mean they can diverge).
    2. Running totals (played/won/drawn/lost/goals/points) via a window
       SUM(...) OVER (PARTITION BY team, season ORDER BY kickoff_utc
       ROWS UNBOUNDED PRECEDING) - i.e. cumulative through and including
       each match.
    3. Position is RANK() partitioned by (season, matchweek) - the round
       number carried on the match itself - using the standard tie-break:
       points desc, goal difference desc, goals for desc (same order
       football-data.org's own table uses). Known simplification: this
       assumes every team has played its matchweek-N fixture by the time
       positions are compared, which can be briefly untrue around
       postponed/rearranged matches - acceptable for this project's scope,
       called out here rather than silently glossed over.
#}

with performance as (
    select * from {{ ref('int_match_team_performance') }}
),

running_totals as (
    select
        team_id,
        season,
        match_id,
        matchweek,
        kickoff_utc,
        row_number() over (
            partition by team_id, season order by kickoff_utc, match_id
        ) as played_games,
        sum(case when result = 'WIN' then 1 else 0 end) over (
            partition by team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as won,
        sum(case when result = 'DRAW' then 1 else 0 end) over (
            partition by team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as drawn,
        sum(case when result = 'LOSS' then 1 else 0 end) over (
            partition by team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as lost,
        sum(goals_for) over (
            partition by team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as goals_for,
        sum(goals_against) over (
            partition by team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as goals_against,
        sum(points) over (
            partition by team_id, season order by kickoff_utc, match_id
            rows between unbounded preceding and current row
        ) as points
    from performance
)

select
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
        partition by season, matchweek
        order by points desc, (goals_for - goals_against) desc, goals_for desc
    ) as league_position
from running_totals
