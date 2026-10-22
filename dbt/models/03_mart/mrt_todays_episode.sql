{{ config(materialized='table') }}

with available_episodes as (
  
  select * from {{ ref('int_episodes') }}
  where air_date not in (select air_date from {{ ref('stg_jeopardy_episodes_history') }})

),

episode_selection as (
    
  select air_date from available_episodes
  order by random()
  limit 1

)

select
  *,
  current_timestamp as selection_timestamp
from episode_selection