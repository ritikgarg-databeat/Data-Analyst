"""The automatic EDA overview + deterministic question generator (sections
20/21 of the Phase 5 spec). Both are built purely from an already-computed
`DatasetProfile` (+ one correlation query) — no AI involved, matches the
spec: "Do not call this 'AI-generated' yet. Use deterministic statistical
logic."""

from __future__ import annotations

from pathlib import Path

from app.dataset_hub import query_engine
from app.models.dataset_profile import DatasetProfile

_CORRELATION_NOTABLE_THRESHOLD = 0.3
_MAX_CORRELATION_PAIRS = 10
_MAX_QUESTIONS = 12


def build_overview(profile: DatasetProfile, parquet_path: Path) -> dict:
    numeric = [c for c in profile.columns if c.data_type == "numeric"]
    categorical = [c for c in profile.columns if c.data_type == "categorical"]
    datetime_cols = [c for c in profile.columns if c.data_type == "datetime"]

    missingness = sorted(
        (
            {"column": c.column_name, "null_percentage": c.null_percentage}
            for c in profile.columns
            if c.null_percentage > 0
        ),
        key=lambda m: m["null_percentage"],
        reverse=True,
    )

    distributions = [
        {
            "column": c.column_name,
            "mean": c.mean,
            "median": c.median,
            "std_dev": c.std_dev,
            "quantiles": c.quantiles,
        }
        for c in numeric
    ]

    categorical_summaries = [{"column": c.column_name, "top_values": c.top_values or []} for c in categorical]

    correlations: list[dict] = []
    if len(numeric) >= 2:
        # cap — a wide table shouldn't mean an O(n^2) query burst
        names = [c.column_name for c in numeric][:8]
        matrix = query_engine.correlation_matrix(parquet_path, names, method="pearson")
        for i, a in enumerate(names):
            for j, b in enumerate(names):
                if j <= i:
                    continue
                value = matrix[i][j]
                if value is not None and abs(value) >= _CORRELATION_NOTABLE_THRESHOLD:
                    correlations.append({"column_a": a, "column_b": b, "correlation": value})
        correlations.sort(key=lambda p: abs(p["correlation"]), reverse=True)
        correlations = correlations[:_MAX_CORRELATION_PAIRS]

    date_trends = [
        {
            "column": c.column_name,
            "min_date": c.min_value,
            "max_date": c.max_value,
            "missing_calendar_days": (c.extra or {}).get("missing_calendar_days"),
        }
        for c in datetime_cols
    ]

    outliers = [
        {"column": c.column_name, "outlier_count": c.outlier_count, "method": c.outlier_method}
        for c in numeric
        if c.outlier_count
    ]

    return {
        "table_name": profile.table_name,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "duplicate_row_count": profile.duplicate_row_count,
        "missingness": missingness,
        "distributions": distributions,
        "categorical_summaries": categorical_summaries,
        "correlations": correlations,
        "date_trends": date_trends,
        "outliers": outliers,
        "generated_at": profile.generated_at.isoformat(),
    }


def generate_questions(profile: DatasetProfile) -> list[dict]:
    numeric = [c.column_name for c in profile.columns if c.data_type == "numeric"]
    categorical = [c.column_name for c in profile.columns if c.data_type == "categorical"]
    datetime_cols = [c.column_name for c in profile.columns if c.data_type == "datetime"]

    questions: list[dict] = []

    for cat in categorical[:2]:
        for num in numeric[:2]:
            question = f"Which {cat} values have the highest total {num}? Which have the lowest?"
            questions.append({"question": question, "category": "segmentation"})

    for num in numeric[:3]:
        question = (
            f"What does the distribution of {num} look like — roughly symmetric, or skewed by a few "
            "large values?"
        )
        questions.append({"question": question, "category": "distribution"})

    for date_col in datetime_cols[:1]:
        for num in numeric[:2]:
            question = (
                f"How does {num} change over time when aggregated by {date_col}? Any trend or seasonality?"
            )
            questions.append({"question": question, "category": "trend"})

    if len(categorical) >= 2:
        question = (
            f"Do {categorical[0]} segments differ meaningfully when you also break them down by "
            f"{categorical[1]}?"
        )
        questions.append({"question": question, "category": "segmentation"})

    if len(numeric) >= 2:
        question = (
            f"Are {numeric[0]} and {numeric[1]} correlated? If so, what business explanation would you "
            "propose — and could it be coincidental?"
        )
        questions.append({"question": question, "category": "correlation"})

    if any(c.outlier_count for c in profile.columns if c.data_type == "numeric"):
        outlier_cols = [
            c.column_name for c in profile.columns if c.data_type == "numeric" and c.outlier_count
        ]
        question = (
            f"The potential outliers in {outlier_cols[0]} — are they data errors to investigate, or "
            "legitimate extreme business cases worth keeping?"
        )
        questions.append({"question": question, "category": "quality"})

    if profile.duplicate_row_count:
        question = (
            f"This table has {profile.duplicate_row_count:,} fully duplicate row(s) — what in the data "
            "collection or import process might explain that?"
        )
        questions.append({"question": question, "category": "quality"})

    if any(c.null_percentage >= 5 for c in profile.columns):
        worst = max(profile.columns, key=lambda c: c.null_percentage)
        question = (
            f"'{worst.column_name}' is missing in {worst.null_percentage:.1f}% of rows — is that "
            "missingness random, or does it cluster around a specific segment?"
        )
        questions.append({"question": question, "category": "quality"})

    questions.append(
        {
            "question": (
                "Write three business-framed insights this dataset supports, each with the evidence "
                "behind it."
            ),
            "category": "storytelling",
        }
    )

    return questions[:_MAX_QUESTIONS]
