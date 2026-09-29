{#
    Grain: one row per team per season - scoring/conceding profile, for
    the "goal analysis" dashboard page.
#}

with performance as (
    select * from {{ ref('int_match_team_performance') }}
)

select
    team_id,
    season,
    count(*)                                              as played,
    sum(goals_for)                                        as goals_for,
    sum(goals_against)                                     as goals_against,
    round(sum(goals_for) / nullif(count(*), 0), 2)          as goals_for_per_match,
    round(sum(goals_against) / nullif(count(*), 0), 2)      as goals_against_per_match,
    sum(case when goals_against = 0 then 1 else 0 end)      as clean_sheets,
    round(100.0 * sum(case when goals_against = 0 then 1 else 0 end) / nullif(count(*), 0), 1) as clean_sheet_pct,
    sum(case when goals_for = 0 then 1 else 0 end)          as matches_failed_to_score,
    round(100.0 * sum(case when goals_for = 0 then 1 else 0 end) / nullif(count(*), 0), 1) as failed_to_score_pct
from performance
group by team_id, season
