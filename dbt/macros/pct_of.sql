{#
    Null/zero-safe percentage: 100.0 * numerator / denominator, or null when
    the denominator is zero (instead of dbt-duckdb raising a divide-by-zero
    error). Centralizing this in one macro avoids every mart re-writing the
    same `case when x = 0 then null else ... end` guard.

    Usage: {{ pct_of('gross_margin', 'gross_revenue') }}
#}
{% macro pct_of(numerator, denominator) %}
    case
        when {{ denominator }} = 0 or {{ denominator }} is null then null
        else 100.0 * {{ numerator }} / {{ denominator }}
    end
{% endmacro %}
