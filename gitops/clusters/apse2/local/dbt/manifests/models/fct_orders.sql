{{ config(materialized='table') }}

select
    o.order_id,
    o.customer_id,
    c.email as customer_email,
    o.order_status,
    o.ordered_at,
    count(i.line_no) as item_count,
    coalesce(sum(i.line_amount), 0) as order_total
from {{ ref('stg_orders') }} o
join {{ ref('stg_customers') }} c on c.customer_id = o.customer_id
left join {{ ref('stg_order_items') }} i on i.order_id = o.order_id
group by o.order_id, o.customer_id, c.email, o.order_status, o.ordered_at
