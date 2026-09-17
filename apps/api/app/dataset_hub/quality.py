"""Deterministic data quality scoring (section 15 of the Phase 5 spec) —
built entirely from a `TableProfile` (app/dataset_hub/profiling.py), no
extra DuckDB queries. This is explicitly an analytical aid, not a claim of
objective correctness — `methodology` is returned verbatim so the scoring
logic is never a black box (rendered as-is in the Dataset Hub UI)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.dataset_hub.profiling import TableProfile

_WEIGHTS = {"completeness": 0.35, "uniqueness": 0.25, "validity": 0.20, "consistency": 0.20}

METHODOLOGY = (
    "Overall score is a weighted average of four component scores "
    f"(completeness {_WEIGHTS['completeness']:.0%}, uniqueness {_WEIGHTS['uniqueness']:.0%}, "
    f"validity {_WEIGHTS['validity']:.0%}, consistency {_WEIGHTS['consistency']:.0%}). "
    "Completeness = 100% minus the average null rate across columns. "
    "Uniqueness = 100% minus the duplicate-row rate. "
    "Validity = 100% minus the average statistical-outlier rate across numeric columns "
    "(IQR/z-score, see the column profile — an outlier is a signal to review, not automatically invalid). "
    "Consistency = 100% minus the average rate of categorical values that only differ by case or "
    "whitespace (e.g. 'USA' vs 'usa') across categorical columns. "
    "This is an analytical aid to help you decide where to look first, not a claim that the dataset is "
    "objectively X% correct — always use judgment about your specific dataset and use case."
)


@dataclass
class QualityIssue:
    type: str
    detail: str
    severity: str  # low | medium | high
    column: str | None = None


@dataclass
class QualityReport:
    overall_score: float
    completeness_score: float
    uniqueness_score: float
    validity_score: float
    consistency_score: float
    duplicate_row_count: int
    issues: list[QualityIssue] = field(default_factory=list)
    methodology: str = METHODOLOGY


def score_quality(profile: TableProfile) -> QualityReport:
    issues: list[QualityIssue] = []

    if profile.row_count == 0 or not profile.columns:
        return QualityReport(
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            [QualityIssue(type="empty_dataset", detail="This table has no rows to score.", severity="high")],
        )

    completeness = 100.0 - (sum(c.null_percentage for c in profile.columns) / len(profile.columns))
    for c in profile.columns:
        if c.null_percentage >= 20:
            issues.append(
                QualityIssue(
                    type="missing_values",
                    column=c.column_name,
                    detail=f"{c.null_percentage:.1f}% of values are missing.",
                    severity="high" if c.null_percentage >= 50 else "medium",
                )
            )

    duplicate_rate = profile.duplicate_row_count / profile.row_count
    uniqueness = 100.0 * (1 - duplicate_rate)
    if profile.duplicate_row_count > 0:
        issues.append(
            QualityIssue(
                type="duplicate_rows",
                detail=f"{profile.duplicate_row_count:,} fully duplicate row(s) ({duplicate_rate:.1%}).",
                severity="high" if duplicate_rate >= 0.05 else "medium",
            )
        )

    numeric_cols = [c for c in profile.columns if c.data_type == "numeric" and c.outlier_count is not None]
    if numeric_cols:
        outlier_rates = [c.outlier_count / profile.row_count for c in numeric_cols]  # type: ignore[operator]
        validity = 100.0 * (1 - sum(outlier_rates) / len(outlier_rates))
        for c, rate in zip(numeric_cols, outlier_rates, strict=True):
            if rate >= 0.02:
                issues.append(
                    QualityIssue(
                        type="outliers",
                        column=c.column_name,
                        detail=(
                            f"{c.outlier_count:,} potential outlier(s) ({rate:.1%}) by the "
                            f"{c.outlier_method} method."
                        ),
                        severity="medium",
                    )
                )
    else:
        validity = 100.0

    categorical_cols = [
        c for c in profile.columns if c.data_type in ("categorical", "text") and c.unique_count
    ]
    inconsistent = [c for c in categorical_cols if c.extra and c.extra.get("case_insensitive_merge_count")]
    if categorical_cols:
        rates = [
            (c.extra.get("case_insensitive_merge_count", 0) / c.unique_count) if c.extra else 0.0
            for c in categorical_cols
        ]
        consistency = 100.0 * (1 - sum(rates) / len(rates))
    else:
        consistency = 100.0
    for c in inconsistent:
        merge_count = c.extra["case_insensitive_merge_count"]  # type: ignore[index]
        issues.append(
            QualityIssue(
                type="inconsistent_categories",
                column=c.column_name,
                detail=(
                    f"{merge_count} value(s) appear to be the same category written inconsistently "
                    "(differing only by case/whitespace)."
                ),
                severity="low",
            )
        )

    completeness = round(max(completeness, 0.0), 1)
    uniqueness = round(max(uniqueness, 0.0), 1)
    validity = round(max(validity, 0.0), 1)
    consistency = round(max(consistency, 0.0), 1)
    overall = round(
        completeness * _WEIGHTS["completeness"]
        + uniqueness * _WEIGHTS["uniqueness"]
        + validity * _WEIGHTS["validity"]
        + consistency * _WEIGHTS["consistency"],
        1,
    )

    issues.sort(key=lambda i: {"high": 0, "medium": 1, "low": 2}[i.severity])

    return QualityReport(
        overall_score=overall,
        completeness_score=completeness,
        uniqueness_score=uniqueness,
        validity_score=validity,
        consistency_score=consistency,
        duplicate_row_count=profile.duplicate_row_count,
        issues=issues,
    )
