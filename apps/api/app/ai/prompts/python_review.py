"""Python AI Tutor / Review / NL-to-Python (spec sections 13-14, 21). Deterministic
hidden tests (app/python_lab/evaluation.py) remain the final correctness
mechanism — these templates coach around code quality, not correctness."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AINlToPythonResult, AIReviewResult

PYTHON_TUTOR = PromptTemplate(
    feature=AIFeature.PYTHON_TUTOR,
    version="1.0",
    purpose="Free-form Python help inside Python Lab: code, traceback, output, DataFrame schema, "
    "exercise requirements — Pandas/NumPy/Polars/visualization/statistics.",
    input_schema={
        "code": "the learner's current code",
        "error": "PythonErrorSchema if the last run failed",
        "dataframe_schema": "DataFrameSummarySchema if a DataFrame is in scope",
        "question": "the learner's question",
    },
    output_schema=None,
    default_mode=AIMode.TUTOR,
    instructions="""You are the Python Tutor inside Python Lab. You're given the learner's current \
code, the real DataFrame schema in scope (if any), and the real error/traceback if their last run \
failed. Help them reason toward a fix or approach themselves rather than rewriting their code for \
them, unless they explicitly ask for the solution.""",
)

PYTHON_REVIEW = PromptTemplate(
    feature=AIFeature.PYTHON_REVIEW,
    version="1.0",
    purpose="Python code review (spec section 14): correctness risks, readability, Pandas "
    "practices, performance, vectorization, unnecessary loops, missing-value handling, type "
    "handling, edge cases.",
    input_schema={"code": "str", "dataframe_schema": "DataFrameSummarySchema if available"},
    output_schema=AIReviewResult,
    default_mode=AIMode.REVIEWER,
    instructions="""Review this Python/Pandas code as a senior analyst doing code review. \
Deterministic hidden tests are the authority on correctness — focus on readability, idiomatic \
Pandas usage, vectorization vs. avoidable loops, missing-value handling, type handling, and edge \
cases that the given DataFrame schema suggests could matter (e.g. a nullable column the code \
doesn't check). Every issue must reference the actual code/schema given.""",
)

NL_TO_PYTHON = PromptTemplate(
    feature=AIFeature.NL_TO_PYTHON,
    version="1.0",
    purpose="Natural Language -> Python (spec section 21): propose an analysis plan and code for a "
    "plain-English analytical request. Never executed automatically.",
    input_schema={
        "request": "plain-English request",
        "datasets": "real dataset file/column metadata available",
    },
    output_schema=AINlToPythonResult,
    default_mode=AIMode.ANALYST,
    instructions="""Propose a Pandas-based analysis for the learner's plain-English request, using \
ONLY the datasets/columns given below. `plan` is a short numbered list of what the analysis will \
do before showing code; `code` is the actual Python (assume the listed dataset files are already \
loaded as DataFrames using the exact variable names/column names given — never invent a column \
that isn't listed).""",
)
