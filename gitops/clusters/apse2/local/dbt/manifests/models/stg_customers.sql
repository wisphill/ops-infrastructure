select
    customer_id,
    lower(email) as email,
    full_name,
    country_code,
    created_at
from {{ source('app', 'customers') }}
