-- dbt analyses are compiled (Jinja/refs resolved) but never run or
-- materialized — a place to version-control ad hoc reporting SQL without it
-- becoming part of the warehouse. Compile with `dbt compile --select
-- top_categories_by_margin` and copy the rendered SQL out of target/compiled.
select
    p.category_name,
    count(distinct fo.order_id) as order_count,
    sum(fo.gross_revenue) as total_revenue,
    sum(fo.gross_margin) as total_margin
from {{ ref('fct_orders') }} as fo
join {{ ref('int_order_items_priced') }} as oip
    on fo.order_id = oip.order_id
join {{ ref('dim_products') }} as p
    on oip.product_id = p.product_id
group by p.category_name
order by total_margin desc
