-- 1 row = 1 customer. Dimension table with lifetime order stats.
with customer_orders as (
    select
        customer_id,
        count(*) as lifetime_order_count,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date
    from {{ ref('stg_orders') }}
    group by customer_id
)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country,
    c.signup_date,
    c.customer_segment,
    coalesce(co.lifetime_order_count, 0) as lifetime_order_count,
    co.first_order_date,
    co.most_recent_order_date
from {{ ref('stg_customers') }} as c
left join customer_orders as co
    on c.customer_id = co.customer_id
