{#
    RAW_COMPETITIONS is append-only across ingestion runs (competition
    metadata is re-fetched on every run). Keep only the latest load per
    competition.
#}

with source as (
    select * from {{ source('raw', 'raw_competitions') }}
),

latest_per_competition as (
    select
        competition_code,
        raw_json,
        loaded_at,
        row_number() over (
            partition by competition_code
            order by loaded_at desc
        ) as row_num
    from source
)

select
    competition_code,
    raw_json:id::number                as competition_id,
    raw_json:name::string               as competition_name,
    raw_json:code::string               as competition_code_from_api,
    raw_json:type::string               as competition_type,
    raw_json:area:name::string          as area_name,
    raw_json:area:code::string          as area_code,
    raw_json:currentSeason:id::number   as current_season_id,
    raw_json:currentSeason:startDate::date  as current_season_start_date,
    raw_json:currentSeason:endDate::date    as current_season_end_date,
    raw_json:currentSeason:currentMatchday::number as current_matchday,
    loaded_at
from latest_per_competition
where row_num = 1
