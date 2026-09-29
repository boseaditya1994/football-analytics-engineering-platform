{#
    Unpivots each match into two team-perspective rows (home and away).
    This is the reusable building block for fact_team_match and for
    deterministically deriving league standings from match results - see
    int_table_progression.sql and docs/data_model.md for the algorithm.

    Only FINISHED matches produce a result/points; unplayed matches are
    excluded here (they contribute zero to any cumulative table).
#}

with matches as (
    select * from {{ ref('stg_matches') }}
    where match_status = 'FINISHED'
),

home_perspective as (
    select
        match_id,
        competition_code,
        season,
        matchweek,
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
