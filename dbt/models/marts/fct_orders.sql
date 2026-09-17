-- Transaction fact: 1 row = 1 order, at the grain of the order itself.
-- One row is created the moment an order exists; it is not re-created per
-- event, which is what distinguishes a transaction fact from a snapshot fact.
with order_items_agg as (
    select
        order_id,
        count(*) as item_count,
        sum(quantity) as total_quantity,
        sum(line_revenue) as gross_revenue,
        sum(line_margin) as gross_margin
    from {{ ref('int_order_items_priced') }}
    group by order_id
)

select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status,
    o.channel,
    cl.channel_display_name,
    coalesce(oi.item_count, 0) as item_count,
    coalesce(oi.total_quantity, 0) as total_quantity,
    coalesce(oi.gross_revenue, 0) as gross_revenue,
    coalesce(oi.gross_margin, 0) as gross_margin,
    {{ pct_of('oi.gross_margin', 'oi.gross_revenue') }} as gross_margin_pct,
    coalesce(op.amount_paid, 0) as amount_paid,
    coalesce(op.amount_refunded, 0) as amount_refunded,
    op.payment_count,
    op.last_payment_date
from {{ ref('stg_orders') }} as o
left join order_items_agg as oi
    on o.order_id = oi.order_id
left join {{ ref('int_order_payments') }} as op
    on o.order_id = op.order_id
left join {{ ref('seed_channel_labels') }} as cl
    on o.channel = cl.channel
