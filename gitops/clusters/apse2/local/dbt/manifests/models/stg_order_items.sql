select
    order_id,
    line_no,
    product_id,
    quantity,
    unit_price,
    quantity * unit_price as line_amount
from {{ source('app', 'order_items') }}
