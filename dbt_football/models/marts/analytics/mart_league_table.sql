{#
    Grain: one row per competition per team per season - the CURRENT
    standings (latest matchweek each team has played), with recent form
    attached. Powers the dashboard's league table view.
#}

with latest_matchweek_per_team as (
    select
        *,
        row_number() over (
            partition by competition_code, team_id, season order by matchweek desc
        ) as row_num
    from {{ ref('fact_standing_snapshot') }}
),

current_standings as (
    select * from latest_matchweek_per_team where row_num = 1
),

latest_form as (
    select
        *,
        row_number() over (
            partition by competition_code, team_id, season order by kickoff_utc desc
        ) as row_num
    from {{ ref('mart_team_form') }}
)

select
    s.competition_code,
    s.team_id,
    t.team_name,
    t.team_crest_url,
    s.season,
    s.league_position,
    s.played_games,
    s.won,
    s.drawn,
    s.lost,
    s.goals_for,
    s.goals_against,
    s.goal_difference,
    s.points,
    round(s.points / nullif(s.played_games, 0), 2) as points_per_game,
    f.form_last_5
from current_standings s
join {{ ref('dim_team') }} t on t.team_id = s.team_id
left join latest_form f
    on f.competition_code = s.competition_code
   and f.team_id = s.team_id
   and f.season = s.season
   and f.row_num = 1
order by s.competition_code, s.season desc, s.league_position
