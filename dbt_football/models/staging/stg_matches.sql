{#
    RAW_MATCHES holds one row per match per ingestion run - a match is
    re-fetched every daily run while its season is current, so scores/status
    can change. Keep the latest load per match_id.
#}

with source as (
    select * from {{ source('raw', 'raw_matches') }}
),

latest_per_match as (
    select
        competition_code,
        season,
        match_id,
        raw_json,
        loaded_at,
        row_number() over (
            partition by match_id
            order by loaded_at desc
        ) as row_num
    from source
)

select
    match_id,
    competition_code,
    season,
    raw_json:matchday::number         as matchweek,
    raw_json:utcDate::timestamp_ntz   as kickoff_utc,
    raw_json:status::string           as match_status,
    raw_json:stage::string            as match_stage,
    raw_json:homeTeam:id::number      as home_team_id,
    raw_json:homeTeam:name::string    as home_team_name,
    raw_json:awayTeam:id::number      as away_team_id,
    raw_json:awayTeam:name::string    as away_team_name,
    raw_json:score:winner::string             as winner,
    raw_json:score:fullTime:home::number      as full_time_home_goals,
    raw_json:score:fullTime:away::number      as full_time_away_goals,
    raw_json:score:halfTime:home::number      as half_time_home_goals,
    raw_json:score:halfTime:away::number      as half_time_away_goals,
    loaded_at
from latest_per_match
where row_num = 1
