{#
    Standard date dimension, generated via dbt_utils.date_spine. Static
    bounds rather than a dynamic min/max query - a few thousand extra rows
    on an XSMALL warehouse costs nothing, and it comfortably covers the
    ingested seasons plus headroom for future ones.
#}

with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2023-01-01' as date)",
        end_date="cast('2029-12-31' as date)"
    ) }}
)

select
    date_day                          as date_key,
    date_day,
    year(date_day)                    as year,
    month(date_day)                   as month,
    day(date_day)                     as day_of_month,
    dayname(date_day)                 as day_name,
    quarter(date_day)                 as quarter,
    weekofyear(date_day)              as week_of_year,
    dayofweekiso(date_day) in (6, 7)  as is_weekend
from spine
