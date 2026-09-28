{#
    A match must never have the same team as both home and away.
    Test passes when this query returns zero rows.
#}

select match_id, home_team_id, away_team_id
from {{ ref('stg_matches') }}
where home_team_id = away_team_id
