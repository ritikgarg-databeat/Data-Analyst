"""Funnel and cohort-retention analysis (Phase 6, spec sections 36-38) —
same one-connection-per-call DuckDB posture as query_engine.py in this
package. `column`/`event` arguments are expected to already be validated by
the calling service before interpolation (see that module's docstring).

Funnel definition used here (documented, not hidden): a user "reaches" step
N if they have an event row matching that step name at any time — this is
the simple/unordered funnel (common for a first funnel analysis). It does
not require step events to happen in strict chronological order per user;
a stricter ordered funnel is a natural follow-up exercise, not built here.
"""

from __future__ import annotations

from pathlib import Path

from app.core.errors import AppError
from app.dataset_hub.query_engine import _connect, _quote

_GRANULARITY_TRUNC = {"day": "day", "week": "week", "month": "month"}


def funnel_conversion(
    parquet_path: Path, user_col: str, event_col: str, steps: list[str], file_format: str = "parquet"
) -> list[dict]:
    if len(steps) < 2:
        raise AppError("A funnel needs at least 2 steps.")
    con = _connect(parquet_path, file_format)
    uq, eq = _quote(user_col), _quote(event_col)
    try:
        result: list[dict] = []
        previous_users: set | None = None
        first_step_users_count: int | None = None
        for step in steps:
            rows = con.execute(f"SELECT DISTINCT {uq} FROM t WHERE {eq} = ?", [step]).fetchall()
            step_users = {r[0] for r in rows}
            reached_users = step_users if previous_users is None else step_users & previous_users
            count = len(reached_users)
            if first_step_users_count is None:
                first_step_users_count = count or 1  # avoid div-by-zero if step 1 is empty
            previous_step_count = len(previous_users) if previous_users is not None else count
            result.append(
                {
                    "step": step,
                    "users": count,
                    "conversion_from_previous": (count / previous_step_count) if previous_step_count else 0.0,
                    "conversion_from_start": count / first_step_users_count,
                    "drop_off": (previous_step_count - count) if previous_users is not None else 0,
                }
            )
            previous_users = reached_users
        return result
    finally:
        con.close()


def cohort_retention_matrix(
    parquet_path: Path,
    user_col: str,
    cohort_date_col: str,
    activity_date_col: str,
    *,
    granularity: str = "month",
    periods: int = 6,
    file_format: str = "parquet",
) -> dict:
    trunc = _GRANULARITY_TRUNC.get(granularity)
    if trunc is None:
        raise AppError(f"Unsupported granularity '{granularity}' — use one of {sorted(_GRANULARITY_TRUNC)}.")
    if not (1 <= periods <= 24):
        raise AppError("periods must be between 1 and 24.")

    uq, cq, aq = _quote(user_col), _quote(cohort_date_col), _quote(activity_date_col)
    con = _connect(parquet_path, file_format)
    try:
        con.execute(
            f"""
            CREATE VIEW cohorted AS
            SELECT
                {uq} AS user_id,
                DATE_TRUNC('{trunc}', CAST({cq} AS TIMESTAMP)) AS cohort_period,
                DATE_TRUNC('{trunc}', CAST({aq} AS TIMESTAMP)) AS activity_period
            FROM t
            WHERE {cq} IS NOT NULL AND {aq} IS NOT NULL
                AND CAST({aq} AS TIMESTAMP) >= CAST({cq} AS TIMESTAMP)
            """
        )
        cohort_sizes = con.execute(
            """
            SELECT cohort_period, COUNT(DISTINCT user_id)
            FROM cohorted WHERE activity_period = cohort_period
            GROUP BY cohort_period ORDER BY cohort_period
            """
        ).fetchall()
        if not cohort_sizes:
            return {"cohorts": [], "periods": periods, "granularity": granularity}

        period_offset_expr = {
            "day": "DATEDIFF('day', cohort_period, activity_period)",
            "week": "DATEDIFF('week', cohort_period, activity_period)",
            "month": "DATEDIFF('month', cohort_period, activity_period)",
        }[granularity]
        active = con.execute(
            f"""
            SELECT cohort_period, {period_offset_expr} AS period_offset, COUNT(DISTINCT user_id)
            FROM cohorted
            WHERE {period_offset_expr} BETWEEN 0 AND {periods - 1}
            GROUP BY cohort_period, period_offset
            """
        ).fetchall()
        active_by_cohort: dict = {}
        for cohort_period, offset, count in active:
            active_by_cohort.setdefault(str(cohort_period), {})[int(offset)] = count

        cohorts = []
        for cohort_period, size in cohort_sizes:
            key = str(cohort_period)
            row = active_by_cohort.get(key, {})
            retention = [round((row.get(p, 0) / size) * 100, 1) if size else None for p in range(periods)]
            cohorts.append({"cohort": key, "cohort_size": size, "retention_pct": retention})

        return {"cohorts": cohorts, "periods": periods, "granularity": granularity}
    finally:
        con.close()
