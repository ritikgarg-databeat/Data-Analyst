"""Unit tests for app/dataset_hub/product_analytics_engine.py — pure DuckDB-
against-a-real-file tests, no database/API involved. Covers funnel and
cohort-retention analysis (Phase 6 spec sections 36-38)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.core.errors import AppError
from app.dataset_hub.product_analytics_engine import cohort_retention_matrix, funnel_conversion


def _write_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


class TestFunnel:
    def test_funnel_step_conversion_and_dropoff(self, tmp_path: Path) -> None:
        path = tmp_path / "events.csv"
        _write_csv(
            path,
            ["user_id", "event_name"],
            [
                [1, "signup"], [1, "activated"], [1, "purchased"],
                [2, "signup"], [2, "activated"],
                [3, "signup"],
                [4, "signup"], [4, "activated"], [4, "purchased"],
            ],
        )
        steps = funnel_conversion(
            path, "user_id", "event_name", ["signup", "activated", "purchased"], file_format="csv"
        )
        by_step = {s["step"]: s for s in steps}
        assert by_step["signup"]["users"] == 4
        assert by_step["activated"]["users"] == 3
        assert by_step["purchased"]["users"] == 2
        assert by_step["activated"]["drop_off"] == 1
        assert by_step["purchased"]["conversion_from_start"] == pytest.approx(0.5)

    def test_funnel_requires_two_steps(self, tmp_path: Path) -> None:
        path = tmp_path / "events.csv"
        _write_csv(path, ["user_id", "event_name"], [[1, "signup"]])
        with pytest.raises(AppError):
            funnel_conversion(path, "user_id", "event_name", ["signup"], file_format="csv")

    def test_funnel_defaults_to_parquet_format(self, tmp_path: Path) -> None:
        # file_format defaults to "parquet" for backward compatibility with existing
        # Dataset-Hub-imported (converted-to-parquet) callers.
        import duckdb

        con = duckdb.connect(":memory:")
        con.execute("CREATE TABLE t (user_id INTEGER, event_name VARCHAR)")
        con.execute("INSERT INTO t VALUES (1,'a'),(1,'b'),(2,'a')")
        path = tmp_path / "events.parquet"
        con.execute(f"COPY t TO '{path.as_posix()}' (FORMAT PARQUET)")
        con.close()

        steps = funnel_conversion(path, "user_id", "event_name", ["a", "b"])
        assert {s["step"]: s["users"] for s in steps} == {"a": 2, "b": 1}


class TestCohortRetention:
    def test_cohort_retention_matrix_shape(self, tmp_path: Path) -> None:
        path = tmp_path / "events.csv"
        _write_csv(
            path,
            ["user_id", "signup_date", "event_ts"],
            [
                [1, "2025-01-01", "2025-01-05"],
                [1, "2025-01-01", "2025-02-10"],
                [1, "2025-01-01", "2025-03-15"],
                [2, "2025-01-01", "2025-01-10"],
                [3, "2025-02-01", "2025-02-15"],
                [3, "2025-02-01", "2025-03-20"],
            ],
        )
        result = cohort_retention_matrix(
            path, "user_id", "signup_date", "event_ts", granularity="month", periods=3, file_format="csv"
        )
        cohorts = {c["cohort"][:10]: c for c in result["cohorts"]}
        assert cohorts["2025-01-01"]["cohort_size"] == 2
        assert cohorts["2025-01-01"]["retention_pct"][0] == 100.0
        assert cohorts["2025-01-01"]["retention_pct"][1] == pytest.approx(50.0)
        assert cohorts["2025-02-01"]["cohort_size"] == 1
        assert cohorts["2025-02-01"]["retention_pct"][1] == 100.0

    def test_invalid_granularity_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "events.csv"
        _write_csv(path, ["user_id", "signup_date", "event_ts"], [[1, "2025-01-01", "2025-01-01"]])
        with pytest.raises(AppError):
            cohort_retention_matrix(
                path, "user_id", "signup_date", "event_ts", granularity="fortnight", file_format="csv"
            )

    def test_periods_out_of_range_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "events.csv"
        _write_csv(path, ["user_id", "signup_date", "event_ts"], [[1, "2025-01-01", "2025-01-01"]])
        with pytest.raises(AppError):
            cohort_retention_matrix(
                path, "user_id", "signup_date", "event_ts", periods=100, file_format="csv"
            )

    def test_no_cohorts_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "events.csv"
        _write_csv(path, ["user_id", "signup_date", "event_ts"], [])
        result = cohort_retention_matrix(path, "user_id", "signup_date", "event_ts", file_format="csv")
        assert result["cohorts"] == []
