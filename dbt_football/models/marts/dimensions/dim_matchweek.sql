{#
    Grain: one row per (competition_code, season, matchweek). A thin
    dimension so fact_team_match/fact_standing_snapshot can join to
    matchweek-level attributes (start/end date of the round) without
    repeating the aggregation in every fact.
#}

with matches as (
    select * from {{ ref('stg_matches') }}
)

select
    competition_code,
    season,
    matchweek,
    min(kickoff_utc) as matchweek_start_utc,
    max(kickoff_utc) as matchweek_end_utc,
    count(distinct match_id) as matches_in_week
from matches
where matchweek is not null
group by competition_code, season, matchweek
