"""Unit tests for the automatic EDA overview + question generator
(app/dataset_hub/eda_engine.py) — sections 20/21 of the Phase 5 spec.
Builds lightweight fakes shaped like `DatasetProfile`/`DatasetColumnProfile`
(only the attributes eda_engine.py actually reads) rather than hitting the
database, plus one real Parquet file for the correlation query."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

from app.dataset_hub import eda_engine


def _col(name, data_type, **kwargs) -> SimpleNamespace:
    defaults = {
        "column_name": name,
        "data_type": data_type,
        "null_percentage": 0.0,
        "mean": None,
        "median": None,
        "std_dev": None,
        "quantiles": None,
        "top_values": None,
        "min_value": None,
        "max_value": None,
        "extra": None,
        "outlier_count": None,
        "outlier_method": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _profile(table_name="orders", row_count=100, duplicate_row_count=0, columns=None) -> SimpleNamespace:
    return SimpleNamespace(
        table_name=table_name,
        row_count=row_count,
        column_count=len(columns or []),
        duplicate_row_count=duplicate_row_count,
        columns=columns or [],
        generated_at=datetime.now(UTC),
    )


@pytest.fixture
def parquet_path(tmp_path: Path) -> Path:
    csv_path = tmp_path / "src.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["revenue", "quantity"])
        for i in range(1, 21):
            writer.writerow([i * 10, i])
    parquet_path = tmp_path / "src.parquet"
    con = duckdb.connect(":memory:")
    con.execute(
        f"COPY (SELECT * FROM read_csv_auto('{csv_path.as_posix()}')) TO "
        f"'{parquet_path.as_posix()}' (FORMAT PARQUET)"
    )
    con.close()
    return parquet_path


class TestBuildOverview:
    def test_missingness_is_sorted_worst_first(self, parquet_path: Path) -> None:
        profile = _profile(
            columns=[
                _col("revenue", "numeric", null_percentage=5.0),
                _col("region", "categorical", null_percentage=20.0),
            ]
        )
        overview = eda_engine.build_overview(profile, parquet_path)
        assert overview["missingness"][0]["column"] == "region"
        assert overview["missingness"][1]["column"] == "revenue"

    def test_columns_with_no_missingness_are_excluded(self, parquet_path: Path) -> None:
        profile = _profile(columns=[_col("revenue", "numeric", null_percentage=0.0)])
        overview = eda_engine.build_overview(profile, parquet_path)
        assert overview["missingness"] == []

    def test_distributions_cover_every_numeric_column(self, parquet_path: Path) -> None:
        profile = _profile(
            columns=[
                _col("revenue", "numeric", mean=50.0, median=45.0),
                _col("region", "categorical"),
            ]
        )
        overview = eda_engine.build_overview(profile, parquet_path)
        assert len(overview["distributions"]) == 1
        assert overview["distributions"][0]["column"] == "revenue"

    def test_categorical_summaries_carry_top_values(self, parquet_path: Path) -> None:
        top = [{"value": "US", "count": 10, "percentage": 50.0}]
        profile = _profile(columns=[_col("region", "categorical", top_values=top)])
        overview = eda_engine.build_overview(profile, parquet_path)
        assert overview["categorical_summaries"][0]["top_values"] == top

    def test_correlations_are_computed_for_numeric_columns(self, parquet_path: Path) -> None:
        profile = _profile(columns=[_col("revenue", "numeric"), _col("quantity", "numeric")])
        overview = eda_engine.build_overview(profile, parquet_path)
        # revenue = quantity * 10 in the fixture data, so they're perfectly correlated.
        assert len(overview["correlations"]) == 1
        assert overview["correlations"][0]["correlation"] > 0.99

    def test_weak_correlations_below_threshold_are_excluded(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "weak.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["a", "b"])
            # `a` increases linearly, `b` alternates +-10 with an equal split —
            # analytically near-zero Pearson correlation (~ -0.09), safely
            # under the 0.3 "notable" threshold regardless of DuckDB's exact
            # floating-point result.
            for i in range(20):
                writer.writerow([i, 10 if i % 2 == 0 else -10])
        weak_parquet = tmp_path / "weak.parquet"
        con = duckdb.connect(":memory:")
        con.execute(
            f"COPY (SELECT * FROM read_csv_auto('{csv_path.as_posix()}')) TO "
            f"'{weak_parquet.as_posix()}' (FORMAT PARQUET)"
        )
        con.close()
        profile = _profile(columns=[_col("a", "numeric"), _col("b", "numeric")])
        overview = eda_engine.build_overview(profile, weak_parquet)
        assert overview["correlations"] == []

    def test_date_trends_surface_missing_calendar_days(self, parquet_path: Path) -> None:
        profile = _profile(
            columns=[
                _col(
                    "order_date",
                    "datetime",
                    min_value="2024-01-01",
                    max_value="2024-01-10",
                    extra={"date_span_days": 10, "distinct_calendar_days": 8, "missing_calendar_days": 2},
                )
            ]
        )
        overview = eda_engine.build_overview(profile, parquet_path)
        assert overview["date_trends"][0]["missing_calendar_days"] == 2

    def test_outliers_list_only_columns_with_outliers(self, parquet_path: Path) -> None:
        profile = _profile(
            columns=[
                _col("revenue", "numeric", outlier_count=3, outlier_method="iqr"),
                _col("quantity", "numeric", outlier_count=0),
            ]
        )
        overview = eda_engine.build_overview(profile, parquet_path)
        assert len(overview["outliers"]) == 1
        assert overview["outliers"][0]["column"] == "revenue"


class TestGenerateQuestions:
    def test_generates_segmentation_questions_for_categorical_and_numeric_columns(
        self, parquet_path: Path
    ) -> None:
        profile = _profile(columns=[_col("region", "categorical"), _col("revenue", "numeric")])
        questions = eda_engine.generate_questions(profile)
        assert any("region" in q["question"] and "revenue" in q["question"] for q in questions)

    def test_generates_a_quality_question_when_duplicates_exist(self, parquet_path: Path) -> None:
        profile = _profile(duplicate_row_count=5, columns=[_col("revenue", "numeric")])
        questions = eda_engine.generate_questions(profile)
        assert any(q["category"] == "quality" and "duplicate" in q["question"] for q in questions)

    def test_always_includes_a_storytelling_prompt(self, parquet_path: Path) -> None:
        profile = _profile(columns=[_col("revenue", "numeric")])
        questions = eda_engine.generate_questions(profile)
        assert any(q["category"] == "storytelling" for q in questions)

    def test_never_exceeds_the_question_cap(self, parquet_path: Path) -> None:
        columns = [_col(f"cat{i}", "categorical") for i in range(5)] + [
            _col(f"num{i}", "numeric") for i in range(5)
        ]
        profile = _profile(duplicate_row_count=1, columns=columns)
        questions = eda_engine.generate_questions(profile)
        assert len(questions) <= 12

    def test_questions_require_no_ai_and_are_fully_deterministic(self, parquet_path: Path) -> None:
        profile = _profile(columns=[_col("region", "categorical"), _col("revenue", "numeric")])
        assert eda_engine.generate_questions(profile) == eda_engine.generate_questions(profile)
