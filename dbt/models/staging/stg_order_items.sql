-- 1 row = 1 product line within an order.
select
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    discount,
    (quantity * unit_price) - discount as line_revenue
from {{ source('raw', 'order_items') }}
