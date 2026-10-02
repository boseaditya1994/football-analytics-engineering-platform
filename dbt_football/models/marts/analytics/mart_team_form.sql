{#
    Grain: one row per team per match - rolling "last 5" / "last 10" form
    as of (and including) that match, ordered by kickoff date within each
    team's (competition, season). Powers form sparklines/trend analytics
    (dashboard "recent form" views).

    Partitioned by competition_code as well as team/season: a team's last
    5 Premier League results and last 5 Champions League results are
    different, meaningful things that should never be blended into one
    rolling window just because they fall in the same season.
#}

with performance as (
    select * from {{ ref('int_match_team_performance') }}
),

with_form as (
    select
        match_id,
        competition_code,
        team_id,
        season,
        matchweek,
        kickoff_utc,
        result,
        points,
        goals_for,
        goals_against,

        count(*) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 4 preceding and current row
        ) as matches_in_last_5,
        sum(points) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 4 preceding and current row
        ) as points_last_5,
        sum(goals_for) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 4 preceding and current row
        ) as goals_for_last_5,
        sum(goals_against) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 4 preceding and current row
        ) as goals_against_last_5,
        array_agg(result) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 4 preceding and current row
        ) as form_last_5,

        count(*) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 9 preceding and current row
        ) as matches_in_last_10,
        sum(points) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 9 preceding and current row
        ) as points_last_10,
        sum(goals_for) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 9 preceding and current row
        ) as goals_for_last_10,
        sum(goals_against) over (
            partition by competition_code, team_id, season order by kickoff_utc, match_id
            rows between 9 preceding and current row
        ) as goals_against_last_10
    from performance
)

select
    match_id,
    competition_code,
    team_id,
    season,
    matchweek,
    kickoff_utc,
    result,
    points,

    matches_in_last_5,
    points_last_5,
    round(points_last_5 / nullif(matches_in_last_5, 0), 2) as ppg_last_5,
    goals_for_last_5,
    goals_against_last_5,
    form_last_5,

    matches_in_last_10,
    points_last_10,
    round(points_last_10 / nullif(matches_in_last_10, 0), 2) as ppg_last_10,
    goals_for_last_10,
    goals_against_last_10
from with_form
