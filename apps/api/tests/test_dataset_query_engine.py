"""Unit tests for the ad hoc explorer queries (app/dataset_hub/query_engine.py)
and the chart data/recommendation/mistake-detector engine
(app/dataset_hub/chart_engine.py) — sections 16-18, 22-30 of the Phase 5
spec. Each test builds a tiny real Parquet file in tmp_path."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from app.dataset_hub import chart_engine, query_engine


def _parquet_from_rows(tmp_path: Path, name: str, columns: list[str], rows: list[list]) -> Path:
    csv_path = tmp_path / f"{name}.csv"
    import csv as csv_mod

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv_mod.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    parquet_path = tmp_path / f"{name}.parquet"
    con = duckdb.connect(":memory:")
    con.execute(
        f"COPY (SELECT * FROM read_csv_auto('{csv_path.as_posix()}')) TO "
        f"'{parquet_path.as_posix()}' (FORMAT PARQUET)"
    )
    con.close()
    return parquet_path


class TestDuplicateRows:
    def test_finds_and_counts_duplicate_rows(self, tmp_path: Path) -> None:
        path = _parquet_from_rows(tmp_path, "dupes", ["a", "b"], [[1, "x"], [1, "x"], [2, "y"]])
        columns, rows, count = query_engine.sample_duplicate_rows(path)
        assert count == 1
        assert len(rows) == 2  # both copies of the duplicate are returned

    def test_no_duplicates_returns_empty_sample(self, tmp_path: Path) -> None:
        path = _parquet_from_rows(tmp_path, "unique", ["a"], [[1], [2], [3]])
        _, rows, count = query_engine.sample_duplicate_rows(path)
        assert count == 0
        assert rows == []


class TestOutlierRows:
    def test_iqr_method_finds_the_extreme_value(self, tmp_path: Path) -> None:
        rows = [[v] for v in range(1, 21)] + [[10_000]]
        path = _parquet_from_rows(tmp_path, "outliers", ["value"], rows)
        _, sample, count, lower, upper = query_engine.sample_outlier_rows(path, "value", method="iqr")
        assert count == 1
        assert sample[0][0] == 10_000
        assert lower is not None and upper is not None


class TestCorrelation:
    def test_perfectly_correlated_columns_score_near_one(self, tmp_path: Path) -> None:
        rows = [[i, i * 2] for i in range(1, 11)]
        path = _parquet_from_rows(tmp_path, "corr", ["a", "b"], rows)
        matrix = query_engine.correlation_matrix(path, ["a", "b"], method="pearson")
        assert matrix[0][0] == 1.0
        assert matrix[0][1] > 0.99

    def test_uncorrelated_alternating_values_score_near_zero(self, tmp_path: Path) -> None:
        rows = [[i, (i % 2)] for i in range(1, 21)]
        path = _parquet_from_rows(tmp_path, "uncorr", ["a", "b"], rows)
        matrix = query_engine.correlation_matrix(path, ["a", "b"], method="pearson")
        assert abs(matrix[0][1]) < 0.5


class TestDistribution:
    def test_bins_cover_the_full_range(self, tmp_path: Path) -> None:
        path = _parquet_from_rows(tmp_path, "dist", ["value"], [[v] for v in range(0, 100)])
        result = query_engine.distribution(path, "value", bins=10)
        assert len(result["bins"]) == 10
        assert sum(b["count"] for b in result["bins"]) == 100


class TestTimeSeries:
    def test_aggregates_by_month(self, tmp_path: Path) -> None:
        rows = [
            ["2024-01-05", 10],
            ["2024-01-20", 20],
            ["2024-02-01", 5],
        ]
        path = _parquet_from_rows(tmp_path, "ts", ["order_date", "revenue"], rows)
        points = query_engine.time_series(
            path, "order_date", "revenue", aggregation="SUM", granularity="month"
        )
        assert len(points) == 2
        assert points[0]["value"] == 30
        assert points[1]["value"] == 5


class TestChartRecommendation:
    @pytest.mark.parametrize(
        "x_type,y_type,expected",
        [
            ("datetime", "numeric", "line"),
            ("categorical", "numeric", "bar"),
            ("numeric", "numeric", "scatter"),
            ("categorical", "categorical", "heatmap"),
            ("numeric", None, "histogram"),
            ("categorical", None, "bar"),
        ],
    )
    def test_recommends_the_expected_chart_type(self, x_type, y_type, expected) -> None:
        chart_type, reason = chart_engine.recommend_chart_type(x_type, y_type)
        assert chart_type == expected
        assert reason  # always explains itself


class TestMistakeDetector:
    def test_flags_a_pie_chart_with_too_many_slices(self) -> None:
        warnings = chart_engine.detect_mistakes(
            "pie", category_count=15, series_count=1, has_title_or_labels=True, sorted_bars=True
        )
        assert any("slices" in w for w in warnings)

    def test_flags_unsorted_bars(self) -> None:
        warnings = chart_engine.detect_mistakes(
            "bar", category_count=5, series_count=1, has_title_or_labels=True, sorted_bars=False
        )
        assert any("sorted" in w for w in warnings)

    def test_flags_missing_labels(self) -> None:
        warnings = chart_engine.detect_mistakes(
            "bar", category_count=3, series_count=1, has_title_or_labels=False, sorted_bars=True
        )
        assert any("title or axis labels" in w for w in warnings)

    def test_flags_too_many_series(self) -> None:
        warnings = chart_engine.detect_mistakes(
            "line", category_count=5, series_count=12, has_title_or_labels=True, sorted_bars=True
        )
        assert any("series" in w for w in warnings)

    def test_a_well_formed_chart_has_no_warnings(self) -> None:
        warnings = chart_engine.detect_mistakes(
            "bar", category_count=5, series_count=1, has_title_or_labels=True, sorted_bars=True
        )
        assert warnings == []


class TestBuildChartData:
    def test_bar_chart_aggregates_by_category(self, tmp_path: Path) -> None:
        rows = [["US", 100], ["US", 50], ["UK", 30]]
        path = _parquet_from_rows(tmp_path, "bar", ["country", "revenue"], rows)
        result = chart_engine.build_chart_data(
            path, "bar", {"x": "country", "y": "revenue", "aggregation": "SUM"}
        )
        by_country = dict(zip(result["x_values"], result["series"][0]["y_values"], strict=True))
        assert by_country["US"] == 150
        assert by_country["UK"] == 30

    def test_histogram_returns_bins_summing_to_row_count(self, tmp_path: Path) -> None:
        path = _parquet_from_rows(tmp_path, "hist", ["value"], [[v] for v in range(50)])
        result = chart_engine.build_chart_data(path, "histogram", {"x": "value", "bins": 5})
        assert sum(result["series"][0]["y_values"]) == 50

    def test_scatter_returns_paired_xy_values(self, tmp_path: Path) -> None:
        rows = [[1, 10], [2, 20], [3, 30]]
        path = _parquet_from_rows(tmp_path, "scatter", ["x", "y"], rows)
        result = chart_engine.build_chart_data(path, "scatter", {"x": "x", "y": "y"})
        assert result["x_values"] == [1, 2, 3]
        assert result["series"][0]["y_values"] == [10, 20, 30]

    def test_filters_are_applied_and_parameterized(self, tmp_path: Path) -> None:
        rows = [["US", 100], ["US", 50], ["UK", 30]]
        path = _parquet_from_rows(tmp_path, "filtered", ["country", "revenue"], rows)
        result = chart_engine.build_chart_data(
            path,
            "bar",
            {
                "x": "country",
                "y": "revenue",
                "aggregation": "SUM",
                "filters": [{"column": "country", "operator": "=", "value": "US"}],
            },
        )
        assert result["x_values"] == ["US"]
        assert result["series"][0]["y_values"] == [150]
