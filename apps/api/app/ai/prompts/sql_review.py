"""SQL AI Tutor / Review / Debug / Optimization / NL-to-SQL (spec sections
9-12, 19-20). Five templates, one module, since they share the same real
inputs (query, schema, result, error) and the same deterministic-authority
rule: SQL correctness is always DuckDB/Postgres's own execution, never this
model's opinion."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AIDebugResult, AINlToSqlResult, AIReviewResult

SQL_TUTOR = PromptTemplate(
    feature=AIFeature.SQL_TUTOR,
    version="1.0",
    purpose="Free-form SQL help inside SQL Lab: explaining SQL, debugging, suggesting approaches, "
    "explaining results, spotting join issues, readability, performance — without writing the "
    "learner's query for them unless asked.",
    input_schema={
        "query": "the learner's current SQL",
        "schema": "real table/column metadata",
        "result": "SqlExecutionResultSchema if it's been run",
        "question": "the learner's question",
    },
    output_schema=None,
    default_mode=AIMode.TUTOR,
    instructions="""You are the SQL Tutor inside SQL Lab. You are given the learner's current \
query, the real schema of the tables it references, and (if they've run it) the real execution \
result or error. Help them get to a correct, readable query themselves — explain, point out risks, \
ask a guiding question — rather than silently rewriting their query for them. Only propose a full \
corrected query if they explicitly ask for it or for "the solution".""",
)

SQL_REVIEW = PromptTemplate(
    feature=AIFeature.SQL_REVIEW,
    version="1.0",
    purpose="Review Query (spec section 10): correctness risks, logic, readability, "
    "maintainability, performance, edge cases, business interpretation.",
    input_schema={
        "query": "str",
        "schema": "real table/column metadata",
        "result": "SqlExecutionResultSchema",
    },
    output_schema=AIReviewResult,
    default_mode=AIMode.REVIEWER,
    instructions="""Review this SQL query as a senior analyst doing code review. Deterministic \
execution (already run, result given below) is the authority on whether it's *correct* for the \
data it saw — your job is everything execution can't tell you: hidden correctness risks (e.g. a \
join that could silently duplicate rows on data the current result doesn't happen to expose), \
readability, maintainability, performance, edge cases, and whether the business question is \
actually answered by what this query computes. Every issue you list must reference the actual \
query/schema given, not a generic SQL-review checklist item.""",
)

SQL_DEBUG = PromptTemplate(
    feature=AIFeature.SQL_DEBUG,
    version="1.0",
    purpose="SQL Debugging (spec section 11): explain a real database error using the actual error "
    "text as primary evidence, never a fabricated one.",
    input_schema={
        "query": "str",
        "schema": "real table/column metadata",
        "error_message": "the real DB error",
    },
    output_schema=AIDebugResult,
    default_mode=AIMode.EXPLAINER,
    instructions="""The learner's query failed. The exact error message from the database is given \
below — quote/paraphrase it directly as your primary evidence; never invent a different error or \
guess at one that wasn't given. Explain what happened, why it likely happened given this exact \
query and schema, where in the query the problem is, how to investigate further, and a suggested \
fix.""",
)

SQL_OPTIMIZATION = PromptTemplate(
    feature=AIFeature.SQL_OPTIMIZATION,
    version="1.0",
    purpose="SQL Optimization Coach (spec section 12): suggest unnecessary columns, inefficient "
    "joins, repeated computation, possible indexes/partitioning, aggregation improvements — "
    "clearly separating confirmed issues from potential ones.",
    input_schema={
        "query": "str",
        "schema": "real table/column metadata",
        "execution_time_ms": "int|None",
        "query_plan": "str|None (often unavailable)",
    },
    output_schema=AIReviewResult,
    default_mode=AIMode.COACH,
    instructions="""Coach the learner on query efficiency. You are given the query, the real \
schema (including row counts where known), and the execution time (a query plan may not be \
available — say so rather than inventing one). Put anything you can verify directly from the given \
schema/query text (e.g. "SELECT *" pulling unused columns, an obviously missing join key) in \
`issues` labeled as a confirmed issue in the text; put anything that would depend on data you \
can't see (e.g. "this might benefit from an index" without knowing cardinality) in `suggestions` \
labeled explicitly as a potential optimization, not a confirmed one.""",
)

NL_TO_SQL = PromptTemplate(
    feature=AIFeature.NL_TO_SQL,
    version="1.0",
    purpose="Natural Language -> SQL (spec sections 19-20): generate SQL from a plain-English "
    "request against the real schema, with a step-by-step explanation and stated assumptions. "
    "Never executed automatically — the caller always requires explicit user confirmation first.",
    input_schema={
        "request": "plain-English request",
        "schema": "real table/column metadata for the target database",
    },
    output_schema=AINlToSqlResult,
    default_mode=AIMode.ANALYST,
    instructions="""Translate the learner's plain-English request into a single SQL query against \
EXACTLY the tables/columns given in the schema below — never reference a table or column that \
isn't listed. If the request is ambiguous, make the most reasonable assumption and state it \
explicitly in `assumptions` rather than silently guessing. `explanation_steps` should walk through \
what the query does in the order a reader would read it (filters, joins, grouping, calculations).""",
)
