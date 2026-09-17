-- 1 row = 1 product.
select
    product_id,
    product_name,
    category_id,
    unit_price,
    cost,
    is_active
from {{ source('raw', 'products') }}
