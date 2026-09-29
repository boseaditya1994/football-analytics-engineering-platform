{#
    Grain: one row per match.
    Unique key: match_id
    Foreign keys: home_team_id, away_team_id -> dim_team.team_id
                  match_date -> dim_date.date_key
                  (competition_code, season, matchweek) -> dim_matchweek
    Measures: full_time_home_goals, full_time_away_goals, total_goals,
              goal_difference (home - away)

    Exists alongside fact_team_match (see ADR-005) because some questions
    are naturally match-centric (final score, venue-neutral goal totals)
    rather than team-centric.
#}

with matches as (
    select * from {{ ref('stg_matches') }}
)

select
    match_id,
    competition_code,
    season,
    matchweek,
    kickoff_utc,
    kickoff_utc::date              as match_date,
    match_status,
    match_stage,
    home_team_id,
    home_team_name,
    away_team_id,
    away_team_name,
    full_time_home_goals,
    full_time_away_goals,
    full_time_home_goals + full_time_away_goals as total_goals,
    full_time_home_goals - full_time_away_goals as goal_difference_home_minus_away,
    half_time_home_goals,
    half_time_away_goals,
    winner
from matches
