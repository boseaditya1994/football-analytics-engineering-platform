{#
    Grain: one row per team_id. team_id is football-data.org's own stable
    team identifier, used directly as the natural key - no surrogate key
    is needed since it's already unique, stable across seasons, and never
    reused. Descriptive attributes take the most recently loaded record
    across all seasons a team appears in.
#}

with teams as (
    select * from {{ ref('stg_teams') }}
),

latest_per_team as (
    select
        *,
        row_number() over (partition by team_id order by season desc, loaded_at desc) as row_num
    from teams
)

select
    team_id,
    team_name,
    team_short_name,
    team_tla,
    team_crest_url,
    founded_year,
    club_colors,
    venue_name
from latest_per_team
where row_num = 1
