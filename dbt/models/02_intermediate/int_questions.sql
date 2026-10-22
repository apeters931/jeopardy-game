with base as (

  {% for season in var('seasons') %}

    select *
    from {{ ref('stg_season_' ~ season) }}

    {% if not loop.last %} union all {% endif %}

  {% endfor %}

),

final as (

  select
    row_number() over (order by air_date, round, category, clue_value) as question_id,
    air_date,
    round,
    replace(
      replace(category, chr(92) || chr(34), chr(34)),
      chr(92) || chr(39), chr(39)
    ) as category,
    clue_value as point_value,
    replace(
      replace(question, chr(92) || chr(34), chr(34)),
      chr(92) || chr(39), chr(39)
    ) as question,
    replace(
      replace(answer, chr(92) || chr(34), chr(34)),
      chr(92) || chr(39), chr(39)
    ) as answer,
    case
      when daily_double_value != 0 then true
      when daily_double_value = 0 then false
      else false
    end as is_daily_double,
  from base

)

select * from final
