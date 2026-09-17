"""Unit tests for the profiling engine (app/dataset_hub/profiling.py) —
pure DuckDB-against-a-real-file tests, no database/API involved. Covers
sections 13/14 of the Phase 5 spec: numeric/categorical/datetime/text
profiling, duplicate detection, and outlier detection."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.dataset_hub.profiling import profile_table


def _write_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def _col(profile, name: str):
    return next(c for c in profile.columns if c.column_name == name)


class TestGeneralShape:
    def test_row_and_column_counts(self, tmp_path: Path) -> None:
        path = tmp_path / "t.csv"
        _write_csv(path, ["a", "b"], [[1, "x"], [2, "y"], [3, "z"]])
        profile = profile_table(path, "csv", "t")
        assert profile.row_count == 3
        assert profile.column_count == 2

    def test_empty_table_does_not_crash(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        _write_csv(path, ["a", "b"], [])
        profile = profile_table(path, "csv", "empty")
        assert profile.row_count == 0
        assert profile.duplicate_row_count == 0


class TestNumericProfiling:
    def test_min_max_mean_median_std(self, tmp_path: Path) -> None:
        path = tmp_path / "nums.csv"
        _write_csv(path, ["value"], [[v] for v in [10, 20, 30, 40, 50]])
        profile = profile_table(path, "csv", "nums")
        col = _col(profile, "value")
        assert col.data_type == "numeric"
        assert float(col.min_value) == 10
        assert float(col.max_value) == 50
        assert col.mean == 30
        assert col.median == 30
        assert col.std_dev is not None

    def test_zero_and_negative_counts(self, tmp_path: Path) -> None:
        path = tmp_path / "signed.csv"
        _write_csv(path, ["value"], [[v] for v in [-5, -1, 0, 0, 3, 7]])
        profile = profile_table(path, "csv", "signed")
        col = _col(profile, "value")
        assert col.zero_count == 2
        assert col.negative_count == 2

    def test_outlier_detection_iqr(self, tmp_path: Path) -> None:
        path = tmp_path / "outliers.csv"
        normal = list(range(1, 21))  # 1..20, tight cluster
        rows = [[v] for v in normal] + [[1000]]  # one obvious extreme outlier
        _write_csv(path, ["value"], rows)
        profile = profile_table(path, "csv", "outliers")
        col = _col(profile, "value")
        assert col.outlier_method == "iqr"
        assert col.outlier_count == 1

    def test_null_values_excluded_from_stats_but_counted(self, tmp_path: Path) -> None:
        path = tmp_path / "nulls.csv"
        _write_csv(path, ["value"], [["10"], [""], ["20"], [""], ["30"]])
        profile = profile_table(path, "csv", "nulls")
        col = _col(profile, "value")
        assert col.null_count == 2
        assert col.null_percentage == 40.0
        assert col.mean == 20  # only the 3 non-null values

    def test_a_literal_nan_or_infinity_value_does_not_crash_profiling(self, tmp_path: Path) -> None:
        """Regression test: DuckDB's read_csv_auto parses a literal "NaN"/
        "Infinity" text cell in a numeric column into a real float NaN/Inf
        value (NOT SQL NULL — pandas' default to_csv() writes missing float
        values exactly this way). STDDEV_SAMP used to raise an uncaught
        duckdb.OutOfRangeException on any such column, failing the entire
        table's (and, in the real import pipeline, the entire dataset's)
        profiling with a cryptic low-level error."""
        path = tmp_path / "nonfinite.csv"
        _write_csv(path, ["value"], [["10"], ["NaN"], ["20"], ["Infinity"], ["-Infinity"], ["30"]])

        profile = profile_table(path, "csv", "nonfinite")  # must not raise

        col = _col(profile, "value")
        assert col.data_type == "numeric"
        assert col.mean == 20  # only the 3 finite values (10, 20, 30)
        assert col.min_value == "10.0"
        assert col.max_value == "30.0"


class TestCategoricalProfiling:
    def test_top_values_and_frequencies(self, tmp_path: Path) -> None:
        path = tmp_path / "cats.csv"
        rows = [["US"]] * 5 + [["UK"]] * 3 + [["FR"]] * 2
        _write_csv(path, ["country"], rows)
        profile = profile_table(path, "csv", "cats")
        col = _col(profile, "country")
        assert col.data_type == "categorical"
        assert col.top_values[0]["value"] == "US"
        assert col.top_values[0]["count"] == 5
        assert col.top_values[0]["percentage"] == 50.0

    def test_case_insensitive_duplicate_categories_flagged_via_extra(self, tmp_path: Path) -> None:
        path = tmp_path / "inconsistent.csv"
        rows = [["USA"], ["usa"], ["USA"], [" usa "], ["Canada"]]
        _write_csv(path, ["country"], rows)
        profile = profile_table(path, "csv", "inconsistent")
        col = _col(profile, "country")
        assert col.extra is not None
        assert col.extra["case_insensitive_merge_count"] >= 1


class TestDatetimeProfiling:
    def test_min_max_and_missing_days(self, tmp_path: Path) -> None:
        path = tmp_path / "dates.csv"
        rows = [["2024-01-01"], ["2024-01-02"], ["2024-01-05"]]  # gap: 3rd/4th missing
        _write_csv(path, ["order_date"], rows)
        profile = profile_table(path, "csv", "dates")
        col = _col(profile, "order_date")
        assert col.data_type == "datetime"
        assert col.extra["date_span_days"] == 5
        assert col.extra["distinct_calendar_days"] == 3
        assert col.extra["missing_calendar_days"] == 2


class TestTextProfiling:
    def test_length_distribution(self, tmp_path: Path) -> None:
        path = tmp_path / "text.csv"
        # Many distinct long strings so it's classified as free text, not categorical.
        rows = [[f"a long unique description number {i} with padding text"] for i in range(60)]
        _write_csv(path, ["description"], rows)
        profile = profile_table(path, "csv", "text")
        col = _col(profile, "description")
        assert col.data_type == "text"
        assert col.min_length is not None
        assert col.max_length is not None
        assert col.avg_length is not None


class TestDuplicateDetection:
    def test_fully_duplicate_rows_are_counted(self, tmp_path: Path) -> None:
        path = tmp_path / "dupes.csv"
        _write_csv(path, ["a", "b"], [[1, "x"], [1, "x"], [2, "y"], [1, "x"]])
        profile = profile_table(path, "csv", "dupes")
        assert profile.duplicate_row_count == 2  # two extra copies of (1, "x")

    def test_no_duplicates_reports_zero(self, tmp_path: Path) -> None:
        path = tmp_path / "unique.csv"
        _write_csv(path, ["a"], [[1], [2], [3]])
        profile = profile_table(path, "csv", "unique")
        assert profile.duplicate_row_count == 0


class TestParquetSource:
    def test_profiles_a_parquet_file_directly(self, tmp_path: Path) -> None:
        import duckdb

        csv_path = tmp_path / "src.csv"
        _write_csv(csv_path, ["a"], [[1], [2], [3]])
        parquet_path = tmp_path / "src.parquet"
        con = duckdb.connect(":memory:")
        con.execute(
            f"COPY (SELECT * FROM read_csv_auto('{csv_path.as_posix()}')) TO "
            f"'{parquet_path.as_posix()}' (FORMAT PARQUET)"
        )
        con.close()

        profile = profile_table(parquet_path, "parquet", "src")
        assert profile.row_count == 3


@pytest.mark.parametrize("file_format", ["csv", "json"])
def test_profiling_works_across_supported_formats(tmp_path: Path, file_format: str) -> None:
    if file_format == "csv":
        path = tmp_path / "x.csv"
        _write_csv(path, ["a"], [[1], [2]])
    else:
        path = tmp_path / "x.json"
        path.write_text('[{"a": 1}, {"a": 2}]', encoding="utf-8")
    profile = profile_table(path, file_format, "x")
    assert profile.row_count == 2
