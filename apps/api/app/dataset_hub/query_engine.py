"""Ad hoc DuckDB queries backing the interactive explorers (sections 16-18,
27-30 of the Phase 5 spec) — duplicate/outlier drill-in, correlation,
distribution, and time-series. Each function opens its own short-lived
connection against a `DatasetTable`'s canonical Parquet file (same
one-connection-per-call posture as app/sql/engines/duckdb_engine.py).

Every `column`/`table` argument here is expected to already be validated
against real profiled column names by the calling service (never raw,
unchecked request input) before being interpolated into SQL — see
`app/services/dataset_analysis_service.py`.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from app.core.errors import AppError

_GRANULARITY_TRUNC = {"day": "day", "week": "week", "month": "month", "quarter": "quarter", "year": "year"}

_READ_FUNCTION_BY_FORMAT = {"csv": "read_csv_auto", "parquet": "read_parquet", "json": "read_json_auto"}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _connect(parquet_path: Path, file_format: str = "parquet") -> duckdb.DuckDBPyConnection:
    """`file_format` defaults to "parquet" since every Dataset-Hub-imported
    table (the original caller of this module) is converted to Parquet at
    import time — Phase 6 datasets registered as plain SQL Lab databases
    (e.g. "saas-product", like the pre-existing "ecommerce") stay as CSV and
    pass "csv" explicitly (see product_analytics_engine.py)."""
    read_fn = _READ_FUNCTION_BY_FORMAT.get(file_format)
    if read_fn is None:
        raise AppError(f"Unsupported file format '{file_format}'.")
    con = duckdb.connect(":memory:")
    con.execute(f"CREATE VIEW t AS SELECT * FROM {read_fn}('{parquet_path.as_posix()}')")
    return con


def sample_duplicate_rows(parquet_path: Path, *, limit: int = 20) -> tuple[list[str], list[list], int]:
    con = _connect(parquet_path)
    try:
        columns = [r[0] for r in con.execute("DESCRIBE t").fetchall()]
        row_count = con.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        distinct_count = con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM t)").fetchone()[0]
        duplicate_count = max(row_count - distinct_count, 0)
        if duplicate_count == 0:
            return columns, [], 0
        rows = con.execute(
            f"""
            SELECT * FROM t
            WHERE ({", ".join(_quote(c) for c in columns)}) IN (
                SELECT {", ".join(_quote(c) for c in columns)} FROM t
                GROUP BY {", ".join(_quote(c) for c in columns)}
                HAVING COUNT(*) > 1
            )
            LIMIT {limit}
            """
        ).fetchall()
        return columns, [list(r) for r in rows], duplicate_count
    finally:
        con.close()


def sample_outlier_rows(
    parquet_path: Path, column: str, *, method: str = "iqr", limit: int = 20
) -> tuple[list[str], list[list], int, float | None, float | None]:
    con = _connect(parquet_path)
    q = _quote(column)
    try:
        columns = [r[0] for r in con.execute("DESCRIBE t").fetchall()]
        if method == "zscore":
            mean_v, std_v = con.execute(
                f"SELECT AVG({q}), STDDEV_SAMP({q}) FROM t WHERE {q} IS NOT NULL"
            ).fetchone()
            if not std_v:
                return columns, [], 0, None, None
            lower, upper = mean_v - 3 * std_v, mean_v + 3 * std_v
        else:
            q25, q75 = con.execute(
                f"SELECT QUANTILE_CONT({q}, 0.25), QUANTILE_CONT({q}, 0.75) FROM t WHERE {q} IS NOT NULL"
            ).fetchone()
            if q25 is None or q75 is None:
                return columns, [], 0, None, None
            iqr = q75 - q25
            lower, upper = q25 - 1.5 * iqr, q75 + 1.5 * iqr

        count = con.execute(f"SELECT COUNT(*) FROM t WHERE {q} < {lower} OR {q} > {upper}").fetchone()[0]
        rows = con.execute(f"SELECT * FROM t WHERE {q} < {lower} OR {q} > {upper} LIMIT {limit}").fetchall()
        return columns, [list(r) for r in rows], count, float(lower), float(upper)
    finally:
        con.close()


def correlation_matrix(
    parquet_path: Path, columns: list[str], *, method: str = "pearson"
) -> list[list[float | None]]:
    if method not in ("pearson", "spearman"):
        raise AppError(f"Unsupported correlation method '{method}'.")
    # DuckDB has no built-in Spearman; ranked below when needed
    fn = "CORR" if method == "pearson" else "CORR"
    con = _connect(parquet_path)
    try:
        if method == "spearman":
            # Spearman = Pearson correlation of rank-transformed values.
            ranked_cols = ", ".join(f"RANK() OVER (ORDER BY {_quote(c)}) AS {_quote(c)}" for c in columns)
            con.execute(f"CREATE VIEW ranked AS SELECT {ranked_cols} FROM t")
            source = "ranked"
        else:
            source = "t"
        matrix: list[list[float | None]] = []
        for a in columns:
            row: list[float | None] = []
            for b in columns:
                if a == b:
                    row.append(1.0)
                    continue
                value = con.execute(f"SELECT {fn}({_quote(a)}, {_quote(b)}) FROM {source}").fetchone()[0]
                row.append(None if value is None else round(float(value), 4))
            matrix.append(row)
        return matrix
    finally:
        con.close()


def distribution(parquet_path: Path, column: str, *, bins: int = 20) -> dict:
    con = _connect(parquet_path)
    q = _quote(column)
    try:
        min_v, max_v, mean_v, median_v, std_v, q25, q75 = con.execute(
            f"""SELECT MIN({q}), MAX({q}), AVG({q}), MEDIAN({q}), STDDEV_SAMP({q}),
                       QUANTILE_CONT({q}, 0.25), QUANTILE_CONT({q}, 0.75)
                FROM t WHERE {q} IS NOT NULL"""
        ).fetchone()
        if min_v is None:
            return {
                "bins": [],
                "mean": None,
                "median": None,
                "std_dev": None,
                "quantiles": None,
                "skewness": None,
            }

        bins = max(bins, 1)
        width = (max_v - min_v) / bins if max_v > min_v else 1.0
        histogram = con.execute(
            f"""
            SELECT bucket, COUNT(*) AS c FROM (
                SELECT LEAST(CAST(FLOOR(({q} - {min_v}) / {width}) AS INTEGER), {bins - 1}) AS bucket
                FROM t WHERE {q} IS NOT NULL
            ) GROUP BY bucket ORDER BY bucket
            """
        ).fetchall()
        counts_by_bucket = dict(histogram)
        bin_list = [
            {
                "bin_start": round(min_v + i * width, 4),
                "bin_end": round(min_v + (i + 1) * width, 4),
                "count": counts_by_bucket.get(i, 0),
            }
            for i in range(bins)
        ]
        skewness = None
        if std_v:
            skew_row = con.execute(
                f"SELECT AVG(POWER(({q} - {mean_v}) / {std_v}, 3)) FROM t WHERE {q} IS NOT NULL"
            ).fetchone()
            skewness = None if skew_row[0] is None else round(float(skew_row[0]), 4)

        quantiles = (
            {
                "p25": round(float(q25), 4),
                "p50": round(float(median_v), 4),
                "p75": round(float(q75), 4),
            }
            if q25 is not None
            else None
        )
        return {
            "bins": bin_list,
            "mean": round(float(mean_v), 4) if mean_v is not None else None,
            "median": round(float(median_v), 4) if median_v is not None else None,
            "std_dev": round(float(std_v), 4) if std_v is not None else None,
            "quantiles": quantiles,
            "skewness": skewness,
        }
    finally:
        con.close()


def column_values(parquet_path: Path, column: str, file_format: str = "parquet") -> list[float]:
    """Pulls one numeric column's non-null values out as a plain list — the
    hand-off point from DuckDB into scipy/statsmodels (see app/stats_engine/),
    which need real arrays, not SQL aggregates."""
    con = _connect(parquet_path, file_format)
    q = _quote(column)
    try:
        rows = con.execute(f"SELECT {q} FROM t WHERE {q} IS NOT NULL").fetchall()
        return [float(r[0]) for r in rows]
    finally:
        con.close()


def time_series(
    parquet_path: Path,
    date_column: str,
    metric_column: str,
    *,
    aggregation: str = "SUM",
    granularity: str = "month",
) -> list[dict]:
    if aggregation not in ("SUM", "AVG", "COUNT", "MIN", "MAX"):
        raise AppError(f"Unsupported aggregation '{aggregation}'.")
    trunc = _GRANULARITY_TRUNC.get(granularity)
    if trunc is None:
        raise AppError(f"Unsupported granularity '{granularity}'.")
    dq, mq = _quote(date_column), _quote(metric_column)
    con = _connect(parquet_path)
    try:
        metric_expr = "COUNT(*)" if aggregation == "COUNT" else f"{aggregation}({mq})"
        rows = con.execute(
            f"""
            SELECT DATE_TRUNC('{trunc}', {dq}) AS period, {metric_expr} AS value
            FROM t WHERE {dq} IS NOT NULL
            GROUP BY period ORDER BY period
            """
        ).fetchall()
        points = [
            {"period": str(period), "value": None if value is None else float(value)}
            for period, value in rows
        ]
        # A simple trailing 3-period rolling average — enough to show trend
        # without pulling in a stats library for one line chart overlay.
        window = 3
        for i, point in enumerate(points):
            values = [p["value"] for p in points[max(0, i - window + 1) : i + 1] if p["value"] is not None]
            point["rolling_avg"] = round(sum(values) / len(values), 4) if values else None
        return points
    finally:
        con.close()
