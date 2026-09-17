-- 1 row = 1 order, standardized (column renames, trimmed status).
select
    order_id,
    customer_id,
    order_date,
    trim(lower(status)) as status,
    channel
from {{ source('raw', 'orders') }}
