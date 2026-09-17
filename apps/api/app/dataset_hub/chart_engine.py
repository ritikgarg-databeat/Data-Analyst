"""Chart data querying + the deterministic recommendation/mistake-detector
helpers (sections 22-27 of the Phase 5 spec). Rendering itself always
happens client-side via react-plotly.js — this module only produces the
(x_values, series) shape the frontend hands straight to a Plotly trace.

As with app/dataset_hub/query_engine.py, `table`/column names reaching here
must already be validated by the calling service against real profiled
columns; filter *values* are always bound as DuckDB query parameters, never
string-interpolated."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from app.core.errors import AppError

_AGG_SQL = {"SUM": "SUM", "AVG": "AVG", "MIN": "MIN", "MAX": "MAX", "COUNT": "COUNT"}
_FILTER_OPERATORS = {"=", "!=", ">", "<", ">=", "<="}
_MAX_POINTS = 5000
_MAX_BARS = 200


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _connect(parquet_path: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{parquet_path.as_posix()}')")
    return con


def _build_where(filters: list[dict[str, Any]]) -> tuple[str, list[Any]]:
    if not filters:
        return "", []
    clauses, params = [], []
    for f in filters:
        column, operator, value = f.get("column"), f.get("operator", "="), f.get("value")
        if not column or operator not in _FILTER_OPERATORS:
            raise AppError(f"Unsupported filter: {f}")
        clauses.append(f"{_quote(column)} {operator} ?")
        params.append(value)
    return " WHERE " + " AND ".join(clauses), params


def recommend_chart_type(x_type: str, y_type: str | None) -> tuple[str, str]:
    if x_type == "datetime" and y_type == "numeric":
        return (
            "line",
            "A date on the X axis against a numeric Y axis shows change over time best as a line chart.",
        )
    if x_type == "categorical" and y_type == "numeric":
        return (
            "bar",
            "A category on the X axis against a numeric Y axis compares groups best as a bar chart.",
        )
    if x_type == "numeric" and y_type == "numeric":
        return (
            "scatter",
            "Two numeric variables are best compared as a scatter plot to reveal their relationship.",
        )
    if x_type == "categorical" and y_type == "categorical":
        return "heatmap", "Two categorical variables are best cross-tabulated as a heatmap of counts."
    if x_type == "numeric" and y_type is None:
        return "histogram", "A single numeric variable's distribution is best shown as a histogram."
    if x_type == "categorical" and y_type is None:
        return "bar", "A single categorical variable's frequency is best shown as a bar chart of counts."
    return "bar", "Bar charts are a safe general-purpose default for comparing categories."


def detect_mistakes(
    chart_type: str, *, category_count: int, series_count: int, has_title_or_labels: bool, sorted_bars: bool
) -> list[str]:
    warnings: list[str] = []
    if chart_type in ("pie", "donut") and category_count > 7:
        warnings.append(
            f"This {chart_type} chart has {category_count} slices — pie charts become hard to read past "
            "6-7 categories. Consider a bar chart instead."
        )
    if chart_type == "bar" and category_count > 1 and not sorted_bars:
        warnings.append(
            "Bars aren't sorted by value — an unsorted categorical axis makes comparisons harder to read "
            "at a glance. Consider sorting."
        )
    if not has_title_or_labels:
        warnings.append(
            "This chart has no title or axis labels — add them so it's understandable without extra context."
        )
    if series_count > 8:
        warnings.append(
            f"This chart has {series_count} series/colors — too many series makes a chart hard to read. "
            "Consider filtering or aggregating further."
        )
    if chart_type == "bar" and category_count > _MAX_BARS:
        warnings.append(
            f"{category_count} bars is a lot to compare visually — consider grouping into fewer categories."
        )
    return warnings


def build_chart_data(parquet_path: Path, chart_type: str, config: dict[str, Any]) -> dict[str, Any]:
    x, y, color = config.get("x"), config.get("y"), config.get("color")
    agg = _AGG_SQL.get((config.get("aggregation") or "SUM").upper(), "SUM")
    where_sql, params = _build_where(config.get("filters") or [])
    sort = config.get("sort")

    con = _connect(parquet_path)
    try:
        if chart_type == "histogram":
            return _histogram(con, x, config.get("bins") or 20, where_sql, params)
        if chart_type in ("bar", "pie", "donut"):
            return _categorical_agg(con, x, y, color, agg, where_sql, params, sort)
        if chart_type == "line":
            return _line(con, x, y, color, agg, config.get("date_granularity"), where_sql, params)
        if chart_type == "scatter":
            return _scatter(con, x, y, color, where_sql, params)
        if chart_type == "box":
            return _box(con, x, y, where_sql, params)
        if chart_type == "heatmap":
            return _heatmap(con, x, y, where_sql, params)
        raise AppError(f"Unsupported chart type '{chart_type}'.")
    finally:
        con.close()


def _rows(con: duckdb.DuckDBPyConnection, sql: str, params: list[Any]) -> list[tuple]:
    return con.execute(sql, params).fetchall()


def _categorical_agg(con, x, y, color, agg, where_sql, params, sort) -> dict:
    if not x:
        raise AppError("A category (X axis) is required.")
    metric = "COUNT(*)" if agg == "COUNT" or not y else f"{agg}({_quote(y)})"
    if color:
        rows = _rows(
            con,
            f"SELECT {_quote(x)}, {_quote(color)}, {metric} FROM t{where_sql} "
            f"GROUP BY {_quote(x)}, {_quote(color)} LIMIT {_MAX_BARS * 20}",
            params,
        )
        x_values = sorted({r[0] for r in rows}, key=str)
        by_color: dict[str, dict] = {}
        for xv, cv, val in rows:
            by_color.setdefault(str(cv), {})[xv] = val
        series = [
            {"name": name, "y_values": [group.get(xv) for xv in x_values]}
            for name, group in sorted(by_color.items())
        ]
    else:
        rows = _rows(
            con,
            f"SELECT {_quote(x)}, {metric} FROM t{where_sql} GROUP BY {_quote(x)} LIMIT {_MAX_BARS}",
            params,
        )
        if sort in ("y_desc", "y_asc"):
            rows.sort(key=lambda r: (r[1] is None, r[1]), reverse=(sort == "y_desc"))
        elif sort in ("x_desc", "x_asc"):
            rows.sort(key=lambda r: str(r[0]), reverse=(sort == "x_desc"))
        x_values = [r[0] for r in rows]
        series = [{"name": y or "count", "y_values": [r[1] for r in rows]}]
    return {"x_values": x_values, "series": series}


def _line(con, x, y, color, agg, granularity, where_sql, params) -> dict:
    if not x or not y:
        raise AppError("Both a date (X axis) and a metric (Y axis) are required for a line chart.")
    trunc = granularity or "month"
    x_expr = f"DATE_TRUNC('{trunc}', {_quote(x)})"
    metric = "COUNT(*)" if agg == "COUNT" else f"{agg}({_quote(y)})"
    if color:
        rows = _rows(
            con,
            f"SELECT {x_expr}, {_quote(color)}, {metric} FROM t{where_sql} GROUP BY 1, 2 ORDER BY 1",
            params,
        )
        x_values = sorted({str(r[0]) for r in rows})
        by_color: dict[str, dict] = {}
        for xv, cv, val in rows:
            by_color.setdefault(str(cv), {})[str(xv)] = val
        series = [
            {"name": name, "y_values": [group.get(xv) for xv in x_values]}
            for name, group in sorted(by_color.items())
        ]
    else:
        rows = _rows(con, f"SELECT {x_expr}, {metric} FROM t{where_sql} GROUP BY 1 ORDER BY 1", params)
        x_values = [str(r[0]) for r in rows]
        series = [{"name": y, "y_values": [r[1] for r in rows]}]
    return {"x_values": x_values, "series": series}


def _scatter(con, x, y, color, where_sql, params) -> dict:
    if not x or not y:
        raise AppError("Both X and Y numeric columns are required for a scatter plot.")
    cols = f"{_quote(x)}, {_quote(y)}" + (f", {_quote(color)}" if color else "")
    rows = _rows(con, f"SELECT {cols} FROM t{where_sql} LIMIT {_MAX_POINTS}", params)
    x_values = [r[0] for r in rows]
    if color:
        series = [{"name": "y", "y_values": [r[1] for r in rows], "color_values": [r[2] for r in rows]}]
    else:
        series = [{"name": y, "y_values": [r[1] for r in rows]}]
    return {"x_values": x_values, "series": series}


def _box(con, x, y, where_sql, params) -> dict:
    if not y:
        raise AppError("A numeric column (Y axis) is required for a box plot.")
    if x:
        rows = _rows(con, f"SELECT {_quote(x)}, {_quote(y)} FROM t{where_sql} LIMIT {_MAX_POINTS}", params)
        x_values = [r[0] for r in rows]
        series = [{"name": y, "y_values": [r[1] for r in rows]}]
    else:
        rows = _rows(con, f"SELECT {_quote(y)} FROM t{where_sql} LIMIT {_MAX_POINTS}", params)
        x_values = [y] * len(rows)
        series = [{"name": y, "y_values": [r[0] for r in rows]}]
    return {"x_values": x_values, "series": series}


def _heatmap(con, x, y, where_sql, params) -> dict:
    if not x or not y:
        raise AppError("Two categorical columns are required for a heatmap.")
    rows = _rows(
        con,
        f"SELECT {_quote(x)}, {_quote(y)}, COUNT(*) FROM t{where_sql} "
        f"GROUP BY 1, 2 LIMIT {_MAX_BARS * _MAX_BARS}",
        params,
    )
    x_values = sorted({str(r[0]) for r in rows})
    y_values_axis = sorted({str(r[1]) for r in rows})
    grid = {(str(a), str(b)): c for a, b, c in rows}
    series = [{"name": yv, "y_values": [grid.get((xv, yv), 0) for xv in x_values]} for yv in y_values_axis]
    return {"x_values": x_values, "series": series}


def _histogram(con, x, bins, where_sql, params) -> dict:
    if not x:
        raise AppError("A numeric column (X axis) is required for a histogram.")
    min_v, max_v = _rows(con, f"SELECT MIN({_quote(x)}), MAX({_quote(x)}) FROM t{where_sql}", params)[0]
    if min_v is None:
        return {"x_values": [], "series": [{"name": x, "y_values": []}]}
    bins = max(int(bins), 1)
    width = (max_v - min_v) / bins if max_v > min_v else 1.0
    not_null = f"{_quote(x)} IS NOT NULL"
    combined_where = f"{where_sql} AND {not_null}" if where_sql else f" WHERE {not_null}"
    rows = _rows(
        con,
        f"""SELECT bucket, COUNT(*) FROM (
                SELECT LEAST(CAST(FLOOR(({_quote(x)} - {min_v}) / {width}) AS INTEGER), {bins - 1}) AS bucket
                FROM t{combined_where}
            ) GROUP BY bucket ORDER BY bucket""",
        params,
    )
    counts = dict(rows)
    x_values = [round(min_v + i * width, 4) for i in range(bins)]
    y_values = [counts.get(i, 0) for i in range(bins)]
    return {"x_values": x_values, "series": [{"name": "count", "y_values": y_values}]}
