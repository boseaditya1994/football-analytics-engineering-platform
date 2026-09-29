{#
    The API's reported match winner must agree with the actual scoreline.
    Test passes when this query returns zero rows.
#}

select match_id, winner, full_time_home_goals, full_time_away_goals
from {{ ref('fact_match') }}
where match_status = 'FINISHED'
  and (
        (full_time_home_goals > full_time_away_goals and winner != 'HOME_TEAM')
     or (full_time_home_goals < full_time_away_goals and winner != 'AWAY_TEAM')
     or (full_time_home_goals = full_time_away_goals and winner != 'DRAW')
  )
