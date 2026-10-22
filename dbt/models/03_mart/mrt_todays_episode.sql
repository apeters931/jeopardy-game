{{ config(materialized='table') }}

{% set existing_relation = adapter.get_relation(
    database=this.database,
    schema=this.schema,
    identifier=this.identifier
) %}

with existing_selection as (

  {% if existing_relation is not none %}
    select air_date, selection_timestamp
    from {{ this }}
    where cast(selection_timestamp as date) = current_date
  {% else %}
    select
      cast(null as date) as air_date,
      current_timestamp as selection_timestamp
    where false
  {% endif %}

),

available_episodes as (

  select air_date
  from {{ ref('int_episodes') }}
  where air_date not in (
    select air_date
    from {{ ref('stg_jeopardy_episodes_history') }}
  )

),

episode_selection as (

  select air_date
  from available_episodes
  where not exists (select 1 from existing_selection)
  order by random()
  limit 1

)

select air_date, selection_timestamp
from existing_selection

union all

select air_date, current_timestamp as selection_timestamp
from episode_selection