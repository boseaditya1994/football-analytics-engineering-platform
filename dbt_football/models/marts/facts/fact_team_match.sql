{#
    Grain: one row per team per match (home/away normalized).
    Unique key: (match_id, team_id)
    Foreign keys: team_id, opponent_team_id -> dim_team.team_id
                  match_date -> dim_date.date_key
                  (competition_code, season, matchweek) -> dim_matchweek
    Measures: goals_for, goals_against, goal_difference, points

    This is the workhorse fact for team-centric analytics (points, form,
    home/away splits, rolling metrics, rankings) - see ADR-005 for why it
    exists alongside match-grain fact_match: normalizing home/away into
    one row per team avoids every downstream query having to CASE on
    home vs. away.
#}

select
    match_id,
    competition_code,
    season,
    matchweek,
    kickoff_utc,
    kickoff_utc::date as match_date,
    team_id,
    opponent_team_id,
    is_home,
    goals_for,
    goals_against,
    goal_difference,
    result,
    points
from {{ ref('int_match_team_performance') }}
