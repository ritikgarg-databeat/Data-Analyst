-- Periodic snapshot fact: 1 row = 1 calendar day, summarizing that day's
-- completed-order activity. Unlike fct_orders (one row per order, forever),
-- this grain is re-derived per period — a new day's row appears once the day
-- happens, and never changes shape after that.
--
-- Built incremental: on a normal run it only (re)computes days at or after
-- the current max(order_date) already in the table, instead of rescanning
-- all history every time. `dbt run --full-refresh` rebuilds from scratch.
{{
    config(
        materialized='incremental',
        unique_key='order_date',
        on_schema_change='fail'
    )
}}

select
    o.order_date,
    count(distinct o.order_id) as completed_order_count,
    count(distinct o.customer_id) as distinct_customer_count,
    sum(o.gross_revenue) as total_gross_revenue,
    sum(o.gross_margin) as total_gross_margin,
    sum(o.amount_paid) as total_amount_paid
from {{ ref('fct_orders') }} as o
where o.status = 'completed'

{% if is_incremental() %}
    and o.order_date >= (select coalesce(max(order_date), '1900-01-01') from {{ this }})
{% endif %}

group by o.order_date
