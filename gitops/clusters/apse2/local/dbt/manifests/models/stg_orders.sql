select
    order_id,
    customer_id,
    status as order_status,
    ordered_at
from {{ source('app', 'orders') }}
