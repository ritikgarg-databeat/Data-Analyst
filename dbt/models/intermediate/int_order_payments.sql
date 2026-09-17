-- 1 row = 1 order, payments collapsed into a single paid amount + resolved status.
-- An order can have multiple payment attempts (e.g. a failed retry then a
-- success, or a later refund); this picks the most recent payment as the
-- order's "current" payment status while summing amounts actually paid.
select
    order_id,
    sum(case when status = 'success' then amount else 0 end) as amount_paid,
    sum(case when status = 'refunded' then amount else 0 end) as amount_refunded,
    count(*) as payment_count,
    max(payment_date) as last_payment_date
from {{ ref('stg_payments') }}
group by order_id
