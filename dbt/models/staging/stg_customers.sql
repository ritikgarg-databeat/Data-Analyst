-- 1 row = 1 customer, standardized.
select
    customer_id,
    first_name,
    last_name,
    email,
    country,
    signup_date,
    trim(lower(customer_segment)) as customer_segment
from {{ source('raw', 'customers') }}
