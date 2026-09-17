"""Context Engine (spec section 4) — pure functions turning already-fetched,
real domain objects into small, bounded dicts safe to hand to
`app/ai/gateway.py`. Every function here takes objects a *service* already
fetched through the platform's own existing services (SqlExecutionService,
CaseService, InterviewService, DatasetAnalysisService, ...) — nothing in
this module queries a database itself, and nothing here invents a field
that isn't already present on what it's given.

"Only provide context relevant to the request. Do NOT dump the entire
database/profile into every prompt" — every builder below trims to what a
human coach would actually need to answer the specific question, not every
column/row/attribute the underlying object has."""

from __future__ import annotations

from typing import Any

MAX_ROWS_IN_CONTEXT = 20
MAX_COLUMNS_IN_CONTEXT = 30


def _dump(obj: Any) -> Any:
    """Accepts a Pydantic model, a dataclass-with-__dict__, a dict, or a
    plain value, and returns something JSON-serializable — used throughout so
    callers can pass whatever shape a service already returned."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(obj)
    return obj


# --- SQL Lab -----------------------------------------------------------


def build_sql_context(
    *,
    query: str,
    table_schemas: list[Any] | None = None,
    result: Any | None = None,
    error_message: str | None = None,
    execution_time_ms: int | None = None,
) -> dict:
    context: dict[str, Any] = {"query": query}
    if table_schemas:
        context["schema"] = [_dump(t) for t in table_schemas][:MAX_COLUMNS_IN_CONTEXT]
    if result is not None:
        dumped = _dump(result)
        if isinstance(dumped, dict) and "rows" in dumped:
            dumped = {**dumped, "rows": dumped["rows"][:MAX_ROWS_IN_CONTEXT]}
        context["result"] = dumped
    if error_message:
        context["error_message"] = error_message
    if execution_time_ms is not None:
        context["execution_time_ms"] = execution_time_ms
    return context


# --- Python Lab ----------------------------------------------------------


def build_python_context(
    *,
    code: str,
    error: Any | None = None,
    dataframe_schema: Any | None = None,
    stdout: str | None = None,
) -> dict:
    context: dict[str, Any] = {"code": code}
    if error is not None:
        context["error"] = _dump(error)
    if dataframe_schema is not None:
        dumped = _dump(dataframe_schema)
        if isinstance(dumped, dict) and "preview_rows" in dumped:
            dumped = {**dumped, "preview_rows": dumped["preview_rows"][:MAX_ROWS_IN_CONTEXT]}
        context["dataframe_schema"] = dumped
    if stdout:
        context["stdout"] = stdout[:2000]
    return context


# --- Case Study Engine -----------------------------------------------------


def build_case_public_context(case: Any) -> dict:
    """ONLY the case's public fields — never hints/rubric/reference_solution.
    Mirrors exactly what `CaseSchema` (the public API response) exposes."""
    return {
        "title": getattr(case, "title", None),
        "stakeholder_name": getattr(case, "stakeholder_name", None),
        "stakeholder_role": getattr(case, "stakeholder_role", None),
        "problem_statement": getattr(case, "problem_statement", None),
        "company_context": getattr(case, "company_context", None),
        "business_context": getattr(case, "business_context", None),
        "objective": getattr(case, "objective", None),
        "constraints": getattr(case, "constraints", None) or [],
        "available_datasets": getattr(case, "available_datasets", None) or [],
        "expected_deliverables": getattr(case, "expected_deliverables", None) or [],
    }


def build_case_attempt_context(attempt: Any) -> dict:
    """The learner's own work so far — never invents what they "meant"."""
    return {
        "current_stage": _dump(getattr(attempt, "current_stage", None)),
        "clarification_questions": getattr(attempt, "clarification_questions", None),
        "problem_framing": getattr(attempt, "problem_framing", None),
        "recommendation": getattr(attempt, "recommendation", None),
        "executive_summary": getattr(attempt, "executive_summary", None),
        "selected_dataset_slugs": getattr(attempt, "selected_dataset_slugs", None) or [],
    }


def build_case_interviewer_context(
    *,
    case: Any,
    clarification_guidance: list[str],
    covered_topic_indexes: list[int],
    transcript: list[dict],
) -> dict:
    """`clarification_guidance` (from the real `Case.clarification_guidance`
    content field) describes what a GOOD clarifying question would ask about
    for this case — it is guidance, not a hidden fact database with concrete
    numbers to progressively reveal (the content model has no such field).
    The interviewer therefore never invents a specific number/segment/value
    when a candidate asks a sharp clarifying question; it acknowledges the
    question is on-target (recognizable against `clarification_guidance`)
    and, consistent with how this platform already works end-to-end,
    encourages the candidate toward the case's real `available_datasets`
    rather than fabricating an answer. `covered_topic_indexes` are indexes
    into `clarification_guidance` the candidate has already asked about this
    session, so the interviewer doesn't re-praise the same question twice."""
    uncovered = [g for i, g in enumerate(clarification_guidance) if i not in covered_topic_indexes]
    return {
        "case_public_facts": build_case_public_context(case),
        "what_a_good_clarifying_question_asks_about": uncovered,
        "already_covered_topics": covered_topic_indexes,
        "transcript_so_far": transcript,
    }


# --- Interview Engine ------------------------------------------------------


def build_interview_debrief_context(*, score: Any, question_reviews: list[Any]) -> dict:
    return {
        "interview_score": _dump(score),
        "question_reviews": [
            {
                "title": getattr(q, "title", None),
                "interview_type": _dump(getattr(q, "interview_type", None)),
                "score": getattr(q, "score", None),
                "passed": getattr(q, "passed", None),
                "over_time": getattr(q, "over_time", None),
                "prompt": getattr(q, "prompt", None),
            }
            for q in question_reviews
        ],
    }


# --- Datasets / EDA --------------------------------------------------------


def build_dataset_profile_context(profile: Any) -> dict:
    return _dump(profile)


def build_domain_result_context(result: Any, *, question: str | None = None) -> dict:
    """Every domain coach (Statistics/Experimentation/Product/Business/Data
    Modeling/dbt) just needs the real, already-computed result payload
    verbatim plus the learner's question — no domain-specific reshaping."""
    context: dict[str, Any] = {"result": _dump(result)}
    if question:
        context["question"] = question
    return context
