with base as (

  {% for season in var('seasons') %}

    select air_date
    from {{ ref('stg_season_' ~ season) }}

    {% if not loop.last %} union all {% endif %}

  {% endfor %}

)

select distinct air_date from base
