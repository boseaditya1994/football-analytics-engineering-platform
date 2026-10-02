{#
    Grain: one row per (competition_code, season, matchweek, team) - the
    league/group-stage table as it stood after that round of matches.
    Scoped to table-eligible stages only (see int_table_progression.sql /
    ADR-011) - a cup competition's knockout rounds never appear here.
    Unique key: (competition_code, season, matchweek, team_id)
    Foreign keys: team_id -> dim_team.team_id
                  (competition_code, season, matchweek) -> dim_matchweek

    Independently derived from match results (see
    int_table_progression.sql for the algorithm), NOT copied from
    football-data.org's standings endpoint. The API's own reported table
    is staged separately in stg_standings and compared against this model
    for reconciliation (see docs/reconciliation.md) - this is the
    project's data-quality showcase feature per the project brief.
#}

select
    competition_code,
    team_id,
    season,
    as_of_matchweek    as matchweek,
    as_of_match_id,
    as_of_kickoff_utc,
    league_position,
    played_games,
    won,
    drawn,
    lost,
    goals_for,
    goals_against,
    goal_difference,
    points
from {{ ref('int_table_progression') }}
