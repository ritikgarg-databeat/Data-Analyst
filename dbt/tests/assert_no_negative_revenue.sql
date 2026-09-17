-- Singular test: fails if it returns any rows. Revenue on a real order line
-- should never be negative — a negative value here would mean a data-entry
-- error or a broken discount calculation upstream, not a valid business case.
select order_id, gross_revenue
from {{ ref('fct_orders') }}
where gross_revenue < 0
