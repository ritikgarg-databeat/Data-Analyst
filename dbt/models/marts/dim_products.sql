-- 1 row = 1 product. Dimension table for the marts layer.
select
    p.product_id,
    p.product_name,
    p.category_id,
    c.category_name,
    c.parent_category,
    p.unit_price,
    p.cost,
    p.unit_price - p.cost as unit_margin,
    p.is_active
from {{ ref('stg_products') }} as p
left join {{ ref('stg_categories') }} as c
    on p.category_id = c.category_id
