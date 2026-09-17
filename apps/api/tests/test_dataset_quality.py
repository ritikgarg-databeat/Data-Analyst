"""Unit tests for the quality scoring engine (app/dataset_hub/quality.py) —
pure dataclass-in, dataclass-out tests, no files/DB (section 15 of the
Phase 5 spec)."""

from __future__ import annotations

from app.dataset_hub.profiling import ColumnProfile, TableProfile
from app.dataset_hub.quality import score_quality


def _numeric_col(name="value", null_pct=0.0, outlier_count=0, row_count=100) -> ColumnProfile:
    return ColumnProfile(
        column_name=name,
        data_type="numeric",
        inferred_sql_type="DOUBLE",
        null_count=int(row_count * null_pct / 100),
        null_percentage=null_pct,
        unique_count=row_count,
        unique_percentage=100.0,
        display_order=0,
        outlier_count=outlier_count,
        outlier_method="iqr" if outlier_count else None,
    )


def _categorical_col(name="country", merge_count=0, unique_count=10) -> ColumnProfile:
    return ColumnProfile(
        column_name=name,
        data_type="categorical",
        inferred_sql_type="VARCHAR",
        null_count=0,
        null_percentage=0.0,
        unique_count=unique_count,
        unique_percentage=1.0,
        display_order=1,
        extra={"case_insensitive_merge_count": merge_count} if merge_count else None,
    )


class TestPerfectDataset:
    def test_a_clean_dataset_scores_100_across_the_board(self) -> None:
        profile = TableProfile(
            table_name="t", row_count=100, column_count=1, duplicate_row_count=0, columns=[_numeric_col()]
        )
        report = score_quality(profile)
        assert report.completeness_score == 100.0
        assert report.uniqueness_score == 100.0
        assert report.validity_score == 100.0
        assert report.consistency_score == 100.0
        assert report.overall_score == 100.0
        assert report.issues == []


class TestCompleteness:
    def test_missing_values_lower_completeness_and_are_flagged(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=100,
            column_count=1,
            duplicate_row_count=0,
            columns=[_numeric_col(null_pct=25.0)],
        )
        report = score_quality(profile)
        assert report.completeness_score == 75.0
        assert any(i.type == "missing_values" for i in report.issues)

    def test_high_missingness_is_flagged_high_severity(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=100,
            column_count=1,
            duplicate_row_count=0,
            columns=[_numeric_col(null_pct=60.0)],
        )
        report = score_quality(profile)
        issue = next(i for i in report.issues if i.type == "missing_values")
        assert issue.severity == "high"


class TestUniqueness:
    def test_duplicate_rows_lower_uniqueness_and_are_flagged(self) -> None:
        profile = TableProfile(
            table_name="t", row_count=100, column_count=1, duplicate_row_count=10, columns=[_numeric_col()]
        )
        report = score_quality(profile)
        assert report.uniqueness_score == 90.0
        assert report.duplicate_row_count == 10
        assert any(i.type == "duplicate_rows" for i in report.issues)


class TestValidity:
    def test_outliers_lower_validity_and_are_flagged(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=100,
            column_count=1,
            duplicate_row_count=0,
            columns=[_numeric_col(outlier_count=5)],
        )
        report = score_quality(profile)
        assert report.validity_score == 95.0
        assert any(i.type == "outliers" for i in report.issues)

    def test_no_numeric_columns_scores_full_validity(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=100,
            column_count=1,
            duplicate_row_count=0,
            columns=[_categorical_col()],
        )
        report = score_quality(profile)
        assert report.validity_score == 100.0


class TestConsistency:
    def test_case_inconsistent_categories_lower_consistency_and_are_flagged(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=100,
            column_count=1,
            duplicate_row_count=0,
            columns=[_categorical_col(merge_count=2, unique_count=10)],
        )
        report = score_quality(profile)
        assert report.consistency_score == 80.0
        assert any(i.type == "inconsistent_categories" for i in report.issues)


class TestOverallWeighting:
    def test_overall_is_a_weighted_average_of_the_four_components(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=100,
            column_count=2,
            duplicate_row_count=10,  # uniqueness = 90
            # completeness = 100 - avg(20, 0) = 90; consistency only averages over the
            # one categorical column (1/10 merged) = 90; validity has no outliers = 100.
            columns=[_numeric_col(null_pct=20.0), _categorical_col(merge_count=1, unique_count=10)],
        )
        report = score_quality(profile)
        assert report.completeness_score == 90.0
        assert report.uniqueness_score == 90.0
        assert report.validity_score == 100.0
        assert report.consistency_score == 90.0
        expected = round(90 * 0.35 + 90 * 0.25 + 100 * 0.20 + 90 * 0.20, 1)
        assert report.overall_score == expected

    def test_issues_are_sorted_most_severe_first(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=100,
            column_count=2,
            duplicate_row_count=1,
            columns=[_numeric_col(null_pct=60.0), _categorical_col(merge_count=1, unique_count=10)],
        )
        report = score_quality(profile)
        severities = [i.severity for i in report.issues]
        assert severities == sorted(severities, key=lambda s: {"high": 0, "medium": 1, "low": 2}[s])


class TestEdgeCases:
    def test_empty_table_scores_zero_with_a_clear_issue(self) -> None:
        profile = TableProfile(table_name="t", row_count=0, column_count=0, duplicate_row_count=0, columns=[])
        report = score_quality(profile)
        assert report.overall_score == 0.0
        assert report.issues[0].type == "empty_dataset"

    def test_methodology_text_is_always_present_and_non_empty(self) -> None:
        profile = TableProfile(
            table_name="t",
            row_count=10,
            column_count=1,
            duplicate_row_count=0,
            columns=[_numeric_col(row_count=10)],
        )
        report = score_quality(profile)
        assert "weighted average" in report.methodology
        assert "analytical aid" in report.methodology
