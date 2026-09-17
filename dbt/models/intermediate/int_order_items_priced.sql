-- 1 row = 1 order line, enriched with product cost/category for margin analysis.
select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.discount,
    oi.line_revenue,
    p.category_id,
    p.cost as unit_cost,
    (oi.quantity * p.cost) as line_cost,
    oi.line_revenue - (oi.quantity * p.cost) as line_margin
from {{ ref('stg_order_items') }} as oi
left join {{ ref('stg_products') }} as p
    on oi.product_id = p.product_id
