{{ config(materialized='table') }}

select
    p.product_id,
    p.sku,
    p.product_name,
    coalesce(sum(i.quantity), 0) as units_sold,
    coalesce(sum(i.line_amount), 0) as revenue
from {{ ref('stg_products') }} p
left join {{ ref('stg_order_items') }} i on i.product_id = p.product_id
group by p.product_id, p.sku, p.product_name
