{#
    SCD Type 2 snapshot of each customer's segment over time.

    Uses the `check` strategy (compare customer_segment column-by-column)
    rather than `timestamp`, since the source data has no reliable
    "last updated" column — this is the common real-world case, not the
    textbook-ideal one. Each row this produces carries dbt's own
    dbt_valid_from / dbt_valid_to bookkeeping columns, so a later
    `customer_segment` change (consumer -> business, say) appends a new row
    and closes out the old one instead of overwriting it in place.
#}
{% snapshot customer_segment_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=['customer_segment'],
    )
}}

select
    customer_id,
    customer_segment
from {{ ref('stg_customers') }}

{% endsnapshot %}
