{{ config(materialized='table') }}

select
    c.customer_id,
    c.email,
    c.full_name,
    c.country_code,
    count(f.order_id) as order_count,
    coalesce(sum(f.order_total), 0) as lifetime_value,
    max(f.ordered_at) as last_ordered_at
from {{ ref('stg_customers') }} c
left join {{ ref('fct_orders') }} f on f.customer_id = c.customer_id
group by c.customer_id, c.email, c.full_name, c.country_code
