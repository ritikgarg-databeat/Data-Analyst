"""The automatic profiling engine (sections 13/14 of the Phase 5 spec) —
entirely DuckDB-driven (section 42: "avoid loading entire datasets into
Python when unnecessary"). One `profile_table()` call opens a single DuckDB
connection, classifies every column by inferred type, and runs only the
aggregate queries appropriate to that type (section 13: "do not calculate
inappropriate statistics for every data type")."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from app.sql.engines.base import to_json_safe

_READ_FUNCTION_BY_FORMAT = {"csv": "read_csv_auto", "parquet": "read_parquet", "json": "read_json_auto"}

_NUMERIC_TYPE_PREFIXES = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL")
_DATETIME_TYPES = {"DATE", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE", "TIME"}
_BOOLEAN_TYPES = {"BOOLEAN"}

# A VARCHAR column is treated as "categorical" (frequency-table stats) rather
# than "text" (length-distribution stats) when it doesn't look like free
# text — few distinct values relative to row count, and short values.
_CATEGORICAL_MAX_UNIQUE = 50
_CATEGORICAL_MAX_UNIQUE_RATIO = 0.1


@dataclass
class ColumnProfile:
    column_name: str
    data_type: str  # numeric | categorical | datetime | text | boolean
    inferred_sql_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    display_order: int
    min_value: str | None = None
    max_value: str | None = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    quantiles: dict[str, float] | None = None
    zero_count: int | None = None
    negative_count: int | None = None
    outlier_count: int | None = None
    outlier_method: str | None = None
    top_values: list[dict] | None = None
    sample_values: list | None = None
    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None
    extra: dict | None = None


@dataclass
class TableProfile:
    table_name: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    columns: list[ColumnProfile] = field(default_factory=list)
    size_bytes: int | None = None


def _classify(sql_type: str, unique_count: int, row_count: int) -> str:
    upper = sql_type.upper()
    if upper in _BOOLEAN_TYPES:
        return "boolean"
    if upper in _DATETIME_TYPES or upper.startswith("TIMESTAMP"):
        return "datetime"
    if upper.startswith(_NUMERIC_TYPE_PREFIXES):
        return "numeric"
    if row_count == 0:
        return "text"
    ratio = unique_count / row_count
    if unique_count <= _CATEGORICAL_MAX_UNIQUE or ratio <= _CATEGORICAL_MAX_UNIQUE_RATIO:
        return "categorical"
    return "text"


def _quote(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def profile_table(
    path: Path, file_format: str, table_name: str, *, size_bytes: int | None = None
) -> TableProfile:
    read_fn = _READ_FUNCTION_BY_FORMAT[file_format]
    con = duckdb.connect(":memory:")
    try:
        con.execute(f"CREATE VIEW t AS SELECT * FROM {read_fn}('{path.as_posix()}')")
        described = con.execute("DESCRIBE t").fetchall()  # [(name, type, null, key, default, extra), ...]
        row_count = con.execute("SELECT COUNT(*) FROM t").fetchone()[0]

        duplicate_row_count = 0
        if row_count > 0:
            distinct_count = con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM t)").fetchone()[0]
            duplicate_row_count = max(row_count - distinct_count, 0)

        columns: list[ColumnProfile] = []
        for order, (name, sql_type, *_rest) in enumerate(described):
            columns.append(_profile_column(con, name, sql_type, row_count, order))

        return TableProfile(
            table_name=table_name,
            row_count=row_count,
            column_count=len(columns),
            duplicate_row_count=duplicate_row_count,
            columns=columns,
            size_bytes=size_bytes,
        )
    finally:
        con.close()


def _profile_column(
    con: duckdb.DuckDBPyConnection, name: str, sql_type: str, row_count: int, order: int
) -> ColumnProfile:
    q = _quote(name)
    null_count = con.execute(f"SELECT COUNT(*) FROM t WHERE {q} IS NULL").fetchone()[0]
    unique_count = con.execute(f"SELECT COUNT(DISTINCT {q}) FROM t").fetchone()[0]
    null_pct = (null_count / row_count * 100) if row_count else 0.0
    unique_pct = (unique_count / row_count * 100) if row_count else 0.0

    data_type = _classify(sql_type, unique_count, row_count)
    sample_rows = con.execute(f"SELECT DISTINCT {q} FROM t WHERE {q} IS NOT NULL LIMIT 5").fetchall()
    # DuckDB returns native Python date/datetime/Decimal/bytes objects here,
    # none of which the JSON column type (DatasetColumnProfile.sample_values)
    # can serialize directly.
    sample_values = [to_json_safe(r[0]) for r in sample_rows]

    profile = ColumnProfile(
        column_name=name,
        data_type=data_type,
        inferred_sql_type=sql_type,
        null_count=null_count,
        null_percentage=round(null_pct, 2),
        unique_count=unique_count,
        unique_percentage=round(unique_pct, 2),
        display_order=order,
        sample_values=sample_values,
    )

    if row_count == 0 or null_count == row_count:
        return profile

    if data_type == "numeric":
        _add_numeric_stats(con, q, profile)
    elif data_type == "datetime":
        _add_datetime_stats(con, q, profile, row_count)
    elif data_type == "categorical" or data_type == "boolean":
        _add_categorical_stats(con, q, profile, row_count)
    else:  # text
        _add_text_stats(con, q, profile)

    return profile


def _add_numeric_stats(con: duckdb.DuckDBPyConnection, q: str, profile: ColumnProfile) -> None:
    # `AND isfinite({q})` excludes NaN/Infinity — a real, literal cell value
    # DuckDB's read_csv_auto produces for a text "NaN"/"Infinity" in a numeric
    # column (pandas' default to_csv() writes missing floats exactly this
    # way), NOT SQL NULL, so the existing `IS NOT NULL` filter alone doesn't
    # catch it. Without this, STDDEV_SAMP raised an uncaught
    # duckdb.OutOfRangeException on any such column, failing the entire
    # dataset import (every table, not just the offending column).
    row = con.execute(
        f"""
        SELECT
            MIN({q}), MAX({q}), AVG({q}), STDDEV_SAMP({q}),
            MEDIAN({q}),
            QUANTILE_CONT({q}, 0.25), QUANTILE_CONT({q}, 0.75),
            COUNT(*) FILTER (WHERE {q} = 0),
            COUNT(*) FILTER (WHERE {q} < 0)
        FROM t WHERE {q} IS NOT NULL AND isfinite({q})
        """
    ).fetchone()
    min_v, max_v, mean_v, std_v, median_v, q25, q75, zero_count, negative_count = row
    profile.min_value = None if min_v is None else str(min_v)
    profile.max_value = None if max_v is None else str(max_v)
    profile.mean = None if mean_v is None else float(mean_v)
    profile.median = None if median_v is None else float(median_v)
    profile.std_dev = None if std_v is None else float(std_v)
    profile.zero_count = zero_count
    profile.negative_count = negative_count
    if q25 is not None and q75 is not None:
        profile.quantiles = {
            "p25": float(q25),
            "p50": float(median_v) if median_v is not None else None,
            "p75": float(q75),
        }
        iqr = float(q75) - float(q25)
        lower, upper = float(q25) - 1.5 * iqr, float(q75) + 1.5 * iqr
        if iqr > 0:
            outlier_count = con.execute(
                f"SELECT COUNT(*) FROM t WHERE {q} < {lower} OR {q} > {upper}"
            ).fetchone()[0]
            profile.outlier_count = outlier_count
            profile.outlier_method = "iqr"
        elif std_v:
            outlier_count = con.execute(
                f"SELECT COUNT(*) FROM t WHERE ABS(({q} - {mean_v}) / {std_v}) > 3"
            ).fetchone()[0]
            profile.outlier_count = outlier_count
            profile.outlier_method = "zscore"


def _add_categorical_stats(
    con: duckdb.DuckDBPyConnection, q: str, profile: ColumnProfile, row_count: int
) -> None:
    rows = con.execute(
        f"SELECT {q}, COUNT(*) AS c FROM t WHERE {q} IS NOT NULL GROUP BY {q} ORDER BY c DESC LIMIT 10"
    ).fetchall()
    profile.top_values = [
        {"value": str(value), "count": count, "percentage": round(count / row_count * 100, 2)}
        for value, count in rows
    ]
    if profile.min_value is None and rows:
        values = [str(v) for v, _ in rows]
        profile.min_value, profile.max_value = min(values), max(values)

    # A simple consistency signal used by quality.py: categories that only
    # differ by case/whitespace (e.g. "USA" / "usa " / "Usa") most likely
    # represent the same real-world value inconsistently entered.
    lower_distinct = con.execute(
        f"SELECT COUNT(DISTINCT LOWER(TRIM(CAST({q} AS VARCHAR)))) FROM t WHERE {q} IS NOT NULL"
    ).fetchone()[0]
    if lower_distinct < profile.unique_count:
        profile.extra = {"case_insensitive_merge_count": profile.unique_count - lower_distinct}


def _add_datetime_stats(
    con: duckdb.DuckDBPyConnection, q: str, profile: ColumnProfile, row_count: int
) -> None:
    min_v, max_v, distinct_days = con.execute(
        f"SELECT MIN({q}), MAX({q}), COUNT(DISTINCT CAST({q} AS DATE)) FROM t WHERE {q} IS NOT NULL"
    ).fetchone()
    profile.min_value = None if min_v is None else str(min_v)
    profile.max_value = None if max_v is None else str(max_v)
    if min_v is not None and max_v is not None:
        span_days = con.execute(
            f"SELECT DATE_DIFF('day', CAST('{min_v}' AS DATE), CAST('{max_v}' AS DATE))"
        ).fetchone()[0]
        span_days = (span_days or 0) + 1
        profile.extra = {
            "date_span_days": span_days,
            "distinct_calendar_days": distinct_days,
            "missing_calendar_days": max(span_days - distinct_days, 0),
        }


def _add_text_stats(con: duckdb.DuckDBPyConnection, q: str, profile: ColumnProfile) -> None:
    min_len, max_len, avg_len = con.execute(
        f"SELECT MIN(LENGTH({q})), MAX(LENGTH({q})), AVG(LENGTH({q})) FROM t WHERE {q} IS NOT NULL"
    ).fetchone()
    profile.min_length = min_len
    profile.max_length = max_len
    profile.avg_length = None if avg_len is None else round(float(avg_len), 2)
