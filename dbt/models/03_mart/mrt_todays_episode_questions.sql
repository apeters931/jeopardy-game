with final as (

  select * 
  from {{ ref('int_questions') }}
  where air_date in (select air_date from {{ ref('mrt_todays_episode') }})

)

select * from final
