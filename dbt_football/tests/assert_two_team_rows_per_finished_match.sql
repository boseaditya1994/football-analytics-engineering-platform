{#
    Every finished match must produce exactly two rows in fact_team_match
    (one home, one away). Test passes when this query returns zero rows.
#}

select match_id, count(*) as row_count
from {{ ref('fact_team_match') }}
group by match_id
having count(*) != 2
