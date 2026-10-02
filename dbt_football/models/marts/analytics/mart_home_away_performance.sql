{#
    Grain: one row per competition per team per season - home vs. away
    split, for the "home/away analytics" dashboard page.
#}

with performance as (
    select * from {{ ref('int_match_team_performance') }}
),

splits as (
    select
        competition_code,
        team_id,
        season,
        sum(case when is_home then 1 else 0 end)                              as home_played,
        sum(case when is_home then points else 0 end)                        as home_points,
        sum(case when is_home and result = 'WIN' then 1 else 0 end)          as home_wins,
        sum(case when is_home and result = 'DRAW' then 1 else 0 end)         as home_draws,
        sum(case when is_home and result = 'LOSS' then 1 else 0 end)         as home_losses,
        sum(case when is_home then goals_for else 0 end)                     as home_goals_for,
        sum(case when is_home then goals_against else 0 end)                 as home_goals_against,

        sum(case when not is_home then 1 else 0 end)                         as away_played,
        sum(case when not is_home then points else 0 end)                    as away_points,
        sum(case when not is_home and result = 'WIN' then 1 else 0 end)      as away_wins,
        sum(case when not is_home and result = 'DRAW' then 1 else 0 end)     as away_draws,
        sum(case when not is_home and result = 'LOSS' then 1 else 0 end)     as away_losses,
        sum(case when not is_home then goals_for else 0 end)                 as away_goals_for,
        sum(case when not is_home then goals_against else 0 end)             as away_goals_against
    from performance
    group by competition_code, team_id, season
)

select
    competition_code,
    team_id,
    season,

    home_played,
    home_wins,
    home_draws,
    home_losses,
    home_points,
    round(home_points / nullif(home_played, 0), 2) as home_ppg,
    home_goals_for,
    home_goals_against,
    home_goals_for - home_goals_against as home_goal_difference,
    round(100.0 * home_wins / nullif(home_played, 0), 1) as home_win_pct,

    away_played,
    away_wins,
    away_draws,
    away_losses,
    away_points,
    round(away_points / nullif(away_played, 0), 2) as away_ppg,
    away_goals_for,
    away_goals_against,
    away_goals_for - away_goals_against as away_goal_difference,
    round(100.0 * away_wins / nullif(away_played, 0), 1) as away_win_pct
from splits
