{#
    Grain: one row per (competition_code, season). Derived from the
    matches present in staging rather than the competitions endpoint,
    since that only describes the *current* season - this needs every
    season we've actually ingested.
#}

with matches as (
    select * from {{ ref('stg_matches') }}
)

select
    competition_code,
    season,
    min(kickoff_utc)::date as season_start_date,
    max(kickoff_utc)::date as season_end_date,
    max(matchweek)          as total_matchweeks,
    count(distinct match_id) as total_matches
from matches
group by competition_code, season
