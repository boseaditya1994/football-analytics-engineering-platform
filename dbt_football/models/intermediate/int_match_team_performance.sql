{#
    Unpivots each match into two team-perspective rows (home and away).
    This is the reusable building block for fact_team_match and for
    deterministically deriving league standings from match results - see
    int_table_progression.sql and docs/data_model.md for the algorithm.

    FINISHED and AWARDED matches both produce a result/points; unplayed
    matches are excluded (they contribute zero to any cumulative table).
    AWARDED matches have a real, final scoreline (a forfeit/administrative
    decision, not an in-progress or voided match) and officially count
    toward the standings exactly like a normally-finished match - found by
    testing against real data: a Bundesliga 2024/25 awarded match was
    being silently excluded, undercounting both teams' points/goal
    difference versus the API's own table. See ADR-011.
#}

with matches as (
    select * from {{ ref('stg_matches') }}
    where match_status in ('FINISHED', 'AWARDED')
),

home_perspective as (
    select
        match_id,
        competition_code,
        season,
        matchweek,
        match_stage,
        kickoff_utc,
        home_team_id           as team_id,
        away_team_id           as opponent_team_id,
        true                    as is_home,
        full_time_home_goals    as goals_for,
        full_time_away_goals    as goals_against,
        winner
    from matches
),

away_perspective as (
    select
        match_id,
        competition_code,
        season,
        matchweek,
        match_stage,
        kickoff_utc,
        away_team_id            as team_id,
        home_team_id            as opponent_team_id,
        false                    as is_home,
        full_time_away_goals     as goals_for,
        full_time_home_goals     as goals_against,
        winner
    from matches
),

unioned as (
    select * from home_perspective
    union all
    select * from away_perspective
)

select
    match_id,
    competition_code,
    season,
    matchweek,
    match_stage,
    kickoff_utc,
    team_id,
    opponent_team_id,
    is_home,
    goals_for,
    goals_against,
    goals_for - goals_against as goal_difference,
    case
        when (is_home and winner = 'HOME_TEAM') or (not is_home and winner = 'AWAY_TEAM') then 'WIN'
        when winner = 'DRAW' then 'DRAW'
        else 'LOSS'
    end as result,
    case
        when (is_home and winner = 'HOME_TEAM') or (not is_home and winner = 'AWAY_TEAM') then 3
        when winner = 'DRAW' then 1
        else 0
    end as points
from unioned
