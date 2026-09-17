-- 1 row = 1 payment transaction for an order.
select
    payment_id,
    order_id,
    payment_date,
    amount,
    trim(lower(payment_method)) as payment_method,
    trim(lower(status)) as status
from {{ source('raw', 'payments') }}
