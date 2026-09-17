-- 1 row = 1 product category.
select
    category_id,
    category_name,
    parent_category
from {{ source('raw', 'categories') }}
