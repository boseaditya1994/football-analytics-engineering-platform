{#
    Grain: one row per competition per season per matchweek per team - the
    full league/group-stage table progression over time, with
    position/points deltas vs. the prior matchweek. Powers the "league
    table progression" dashboard page (title race / relegation battle /
    group-stage qualification race over time).
#}

with snapshots as (
    select * from {{ ref('fact_standing_snapshot') }}
),

with_deltas as (
    select
        *,
        lag(league_position) over (
            partition by competition_code, team_id, season order by matchweek
        ) as previous_matchweek_position,
        lag(points) over (
            partition by competition_code, team_id, season order by matchweek
        ) as previous_matchweek_points
    from snapshots
)

select
    competition_code,
    team_id,
    season,
    matchweek,
    league_position,
    played_games,
    won,
    drawn,
    lost,
    goals_for,
    goals_against,
    goal_difference,
    points,
    previous_matchweek_position,
    previous_matchweek_position - league_position as position_change,
    points - coalesce(previous_matchweek_points, 0) as points_gained_this_matchweek
from with_deltas
