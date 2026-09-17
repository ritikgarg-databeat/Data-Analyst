"""Rule -> SQL translation + result interpretation for the Data Quality Lab.

Runs real, read-only SQL against a dataset's own DuckDB-backed tables (via
the same DuckDBEngine the SQL Lab uses — see app/sql/registry.py) so a check
result is an actual query outcome, never a simulated/fabricated one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.models.enums import DataQualityRuleType, DataQualityStatus

_VIOLATION_COUNT_RULES = {
    DataQualityRuleType.NOT_NULL,
    DataQualityRuleType.UNIQUE,
    DataQualityRuleType.ACCEPTED_VALUES,
    DataQualityRuleType.RELATIONSHIP,
    DataQualityRuleType.MIN_MAX,
}


class DataQualityRuleError(Exception):
    """The rule itself is misconfigured (missing a required config key) —
    surfaced as a request-time error, distinct from a check that runs fine
    but fails (that's a normal FAIL DataQualityRun, not an exception)."""


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _quote_literal(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def build_check_sql(
    rule_type: DataQualityRuleType, *, table_name: str, column_name: str | None, config: dict
) -> str:
    """Returns a single read-only SELECT that reduces to one aggregate row —
    a violation count for most rule types, MAX(column) for FRESHNESS, or
    COUNT(*) for ROW_COUNT — interpreted by `interpret_result` below."""
    table = _quote_ident(table_name)

    if rule_type == DataQualityRuleType.NOT_NULL:
        if not column_name:
            raise DataQualityRuleError("NOT_NULL requires a column_name.")
        col = _quote_ident(column_name)
        return f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"

    if rule_type == DataQualityRuleType.UNIQUE:
        if not column_name:
            raise DataQualityRuleError("UNIQUE requires a column_name.")
        col = _quote_ident(column_name)
        return f"SELECT COUNT(*) - COUNT(DISTINCT {col}) FROM {table}"

    if rule_type == DataQualityRuleType.ACCEPTED_VALUES:
        if not column_name:
            raise DataQualityRuleError("ACCEPTED_VALUES requires a column_name.")
        values = config.get("values")
        if not values:
            raise DataQualityRuleError("ACCEPTED_VALUES requires a non-empty 'values' list in config.")
        col = _quote_ident(column_name)
        literals = ", ".join(_quote_literal(v) for v in values)
        return f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} NOT IN ({literals})"

    if rule_type == DataQualityRuleType.RELATIONSHIP:
        if not column_name:
            raise DataQualityRuleError("RELATIONSHIP requires a column_name.")
        to_table = config.get("to_table")
        to_column = config.get("to_column")
        if not to_table or not to_column:
            raise DataQualityRuleError("RELATIONSHIP requires 'to_table' and 'to_column' in config.")
        col = _quote_ident(column_name)
        to_t = _quote_ident(to_table)
        to_c = _quote_ident(to_column)
        return (
            f"SELECT COUNT(*) FROM {table} AS t "
            f"WHERE t.{col} IS NOT NULL "
            f"AND NOT EXISTS (SELECT 1 FROM {to_t} AS r WHERE r.{to_c} = t.{col})"
        )

    if rule_type == DataQualityRuleType.MIN_MAX:
        if not column_name:
            raise DataQualityRuleError("MIN_MAX requires a column_name.")
        col = _quote_ident(column_name)
        min_value = config.get("min")
        max_value = config.get("max")
        conditions = []
        if min_value is not None:
            conditions.append(f"{col} < {min_value}")
        if max_value is not None:
            conditions.append(f"{col} > {max_value}")
        if not conditions:
            raise DataQualityRuleError("MIN_MAX requires 'min' and/or 'max' in config.")
        return f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND ({' OR '.join(conditions)})"

    if rule_type == DataQualityRuleType.FRESHNESS:
        if not column_name:
            raise DataQualityRuleError("FRESHNESS requires a column_name.")
        if config.get("max_age_hours") is None:
            # Without this, interpret_result's `ok = max_age_hours is None or
            # ...` was unconditionally True for a rule saved with no
            # threshold — a real, reachable gap: the UI never required this
            # field either — reporting a false-confidence PASS forever,
            # regardless of how stale the data actually is.
            raise DataQualityRuleError("FRESHNESS requires 'max_age_hours' in config.")
        col = _quote_ident(column_name)
        return f"SELECT MAX({col}) FROM {table}"

    if rule_type == DataQualityRuleType.ROW_COUNT:
        if config.get("min_rows") is None and config.get("max_rows") is None:
            # Same gap as FRESHNESS above, for the same reason: with neither
            # threshold set, interpret_result's ROW_COUNT `ok` expression was
            # unconditionally True.
            raise DataQualityRuleError("ROW_COUNT requires 'min_rows' and/or 'max_rows' in config.")
        return f"SELECT COUNT(*) FROM {table}"

    raise DataQualityRuleError(f"Unsupported rule type: {rule_type}")


@dataclass
class RuleCheckOutcome:
    status: DataQualityStatus
    expected_value: str | None
    actual_value: str | None
    details: dict


def interpret_result(rule_type: DataQualityRuleType, config: dict, value: Any) -> RuleCheckOutcome:
    if rule_type in _VIOLATION_COUNT_RULES:
        violation_count = int(value or 0)
        status = DataQualityStatus.PASS if violation_count == 0 else DataQualityStatus.FAIL
        return RuleCheckOutcome(
            status=status,
            expected_value="0 violations",
            actual_value=f"{violation_count} violation(s)",
            details={"violation_count": violation_count},
        )

    if rule_type == DataQualityRuleType.ROW_COUNT:
        row_count = int(value or 0)
        min_rows = config.get("min_rows")
        max_rows = config.get("max_rows")
        ok = (min_rows is None or row_count >= min_rows) and (max_rows is None or row_count <= max_rows)
        min_label = min_rows if min_rows is not None else 0
        max_label = max_rows if max_rows is not None else "∞"
        expected = f"{min_label}–{max_label} rows"
        return RuleCheckOutcome(
            status=DataQualityStatus.PASS if ok else DataQualityStatus.FAIL,
            expected_value=expected,
            actual_value=f"{row_count} row(s)",
            details={"row_count": row_count},
        )

    if rule_type == DataQualityRuleType.FRESHNESS:
        if value is None:
            return RuleCheckOutcome(
                status=DataQualityStatus.ERROR,
                expected_value=None,
                actual_value=None,
                details={"reason": "No rows, or the column's max value is NULL."},
            )
        if isinstance(value, datetime):
            max_ts = value
        else:
            try:
                max_ts = datetime.fromisoformat(str(value))
            except ValueError:
                # The configured column isn't a real date/timestamp (e.g. a
                # numeric id column) — the free-text column-name input in the
                # UI doesn't scope to date-typed columns, so this is a real,
                # easy mistake to make. A graceful ERROR outcome, not an
                # uncaught crash.
                return RuleCheckOutcome(
                    status=DataQualityStatus.ERROR,
                    expected_value=None,
                    actual_value=str(value),
                    details={"reason": f"'{value}' is not a valid date/timestamp — is this a date column?"},
                )
        if max_ts.tzinfo is None:
            max_ts = max_ts.replace(tzinfo=UTC)

        as_of_raw = config.get("as_of")
        as_of = datetime.fromisoformat(as_of_raw).replace(tzinfo=UTC) if as_of_raw else datetime.now(UTC)
        max_age_hours = config.get("max_age_hours")
        age_hours = (as_of - max_ts).total_seconds() / 3600
        ok = max_age_hours is None or age_hours <= max_age_hours
        return RuleCheckOutcome(
            status=DataQualityStatus.PASS if ok else DataQualityStatus.FAIL,
            expected_value=f"no more than {max_age_hours}h old" if max_age_hours is not None else None,
            actual_value=f"{age_hours:.1f}h old (latest value: {max_ts.isoformat()})",
            details={"age_hours": round(age_hours, 1), "latest_value": max_ts.isoformat()},
        )

    raise DataQualityRuleError(f"Unsupported rule type: {rule_type}")
