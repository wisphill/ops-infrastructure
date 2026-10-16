select
    product_id,
    sku,
    name as product_name,
    unit_price as list_price,
    is_active
from {{ source('app', 'products') }}
