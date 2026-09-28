{#
    RAW_TEAMS holds one row per team per ingestion run. A team can appear in
    multiple seasons; keep the latest load per (team, competition, season).
#}

with source as (
    select * from {{ source('raw', 'raw_teams') }}
),

latest_per_team_season as (
    select
        competition_code,
        season,
        raw_json,
        loaded_at,
        row_number() over (
            partition by competition_code, season, raw_json:id::number
            order by loaded_at desc
        ) as row_num
    from source
)

select
    competition_code,
    season,
    raw_json:id::number          as team_id,
    raw_json:name::string        as team_name,
    raw_json:shortName::string   as team_short_name,
    raw_json:tla::string         as team_tla,
    raw_json:crest::string       as team_crest_url,
    raw_json:founded::number     as founded_year,
    raw_json:clubColors::string  as club_colors,
    raw_json:venue::string       as venue_name,
    loaded_at
from latest_per_team_season
where row_num = 1
