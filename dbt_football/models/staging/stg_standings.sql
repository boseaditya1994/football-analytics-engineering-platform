{#
    API-reported standings, flattened from the nested standings/table arrays.
    This is the source-of-truth-per-provider view used only for
    reconciliation against our independently-derived standings (see
    intermediate/int_table_progression.sql and docs/reconciliation.md) -
    it is never used directly as the analytics mart's standings.

    Keep the latest load per (competition, season, snapshot_date) - one
    ingestion run can produce one row per stage/type/team combination.
#}

with source as (
    select * from {{ source('raw', 'raw_standings') }}
),

latest_per_snapshot as (
    select
        competition_code,
        season,
        snapshot_date,
        raw_json,
        loaded_at,
        row_number() over (
            partition by competition_code, season, snapshot_date
            order by loaded_at desc
        ) as row_num
    from source
    qualify row_num = 1
),

standings_stage as (
    select
        competition_code,
        season,
        snapshot_date,
        loaded_at,
        standings_entry.value:stage::string as stage,
        standings_entry.value:type::string  as standing_type,
        standings_entry.value:table         as team_table
    from latest_per_snapshot,
        lateral flatten(input => raw_json:standings) as standings_entry
),

standings_team as (
    select
        competition_code,
        season,
        snapshot_date,
        loaded_at,
        stage,
        standing_type,
        team_row.value:position::number         as api_position,
        team_row.value:team:id::number           as team_id,
        team_row.value:team:name::string         as team_name,
        team_row.value:playedGames::number       as played_games,
        team_row.value:won::number               as won,
        team_row.value:draw::number              as draw,
        team_row.value:lost::number              as lost,
        team_row.value:points::number            as points,
        team_row.value:goalsFor::number          as goals_for,
        team_row.value:goalsAgainst::number      as goals_against,
        team_row.value:goalDifference::number    as goal_difference
    from standings_stage,
        lateral flatten(input => team_table) as team_row
)

select * from standings_team
where standing_type = 'TOTAL'
