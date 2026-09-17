"""Pydantic models for content/lessons/**/*.yaml and content/exercises/**/*.yaml.

This is the REAL, enforced validation source of truth for content files —
content/schema/*.json and packages/shared/src/content-types.ts are
human-readable mirrors of this module, kept in sync by hand.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Content blocks
# ---------------------------------------------------------------------------

CalloutVariant = Literal["important", "tip", "warning", "interview_tip", "common_mistake"]
CodeLanguage = Literal["sql", "python", "javascript", "yaml", "json", "text"]


class TextBlock(BaseModel):
    type: Literal["text"]
    body: str


class HeadingBlock(BaseModel):
    type: Literal["heading"]
    text: str
    level: Literal[2, 3] = 2


class CalloutBlock(BaseModel):
    type: Literal["callout"]
    variant: CalloutVariant
    title: str | None = None
    body: str


class CodeBlock(BaseModel):
    type: Literal["code"]
    language: CodeLanguage
    code: str
    caption: str | None = None


class OutputBlock(BaseModel):
    type: Literal["output"]
    body: str
    caption: str | None = None


class TableBlock(BaseModel):
    type: Literal["table"]
    headers: list[str]
    rows: list[list[str]]
    caption: str | None = None


class FormulaBlock(BaseModel):
    type: Literal["formula"]
    expression: str
    description: str | None = None


class ImageBlock(BaseModel):
    type: Literal["image"]
    src: str
    alt: str
    caption: str | None = None


class ExampleBlock(BaseModel):
    type: Literal["example"]
    title: str
    body: str
    code: str | None = None
    language: CodeLanguage | None = None


class QuestionBlock(BaseModel):
    type: Literal["question"]
    prompt: str
    choices: list[str]
    correct_index: int
    explanation: str


class ChecklistBlock(BaseModel):
    type: Literal["checklist"]
    title: str | None = None
    items: list[str]


class ComparisonBlock(BaseModel):
    type: Literal["comparison"]
    title: str
    columns: list[str]
    rows: list[list[str]]


ContentBlock = Annotated[
    TextBlock
    | HeadingBlock
    | CalloutBlock
    | CodeBlock
    | OutputBlock
    | TableBlock
    | FormulaBlock
    | ImageBlock
    | ExampleBlock
    | QuestionBlock
    | ChecklistBlock
    | ComparisonBlock,
    Field(discriminator="type"),
]

# ---------------------------------------------------------------------------
# Lesson content file
# ---------------------------------------------------------------------------

CompletionRuleTypeLiteral = Literal["reading_percent", "exercise_score", "assessment_score"]
DifficultyLiteral = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]


class CompletionCriteria(BaseModel):
    type: CompletionRuleTypeLiteral
    threshold: float = Field(ge=0, le=100)


class InterviewQuestionRef(BaseModel):
    question: str
    answer: str


class ResourceRef(BaseModel):
    title: str
    url: str


class LessonContentFile(BaseModel):
    slug: str
    module_slug: str
    title: str
    description: str
    content_type: Literal["READING", "VIDEO", "INTERACTIVE", "EXERCISE", "QUIZ"] = "READING"
    difficulty: DifficultyLiteral
    estimated_minutes: int = Field(gt=0)
    display_order: int = Field(gt=0)
    objectives: list[str] = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    soft_prerequisites: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    related_lessons: list[str] = Field(default_factory=list)
    completion_criteria: CompletionCriteria | None = None
    key_takeaways: list[str] = Field(min_length=1)
    common_mistakes: list[str] = Field(default_factory=list)
    practical_applications: list[str] = Field(default_factory=list)
    interview_questions: list[InterviewQuestionRef] = Field(default_factory=list)
    resources: list[ResourceRef] = Field(default_factory=list)
    blocks: list[ContentBlock] = Field(min_length=1)

    # Path this was loaded from, set by the loader (not part of the file itself).
    source_path: str = ""


# ---------------------------------------------------------------------------
# Exercise content file
# ---------------------------------------------------------------------------

ExerciseTypeLiteral = Literal[
    "MULTIPLE_CHOICE",
    "TRUE_FALSE",
    "SHORT_ANSWER",
    "CODE",
    "SQL",
    "PYTHON",
    "DBT",
    "BUSINESS_REASONING",
    "DATA_INTERPRETATION",
    "MODELING",
    "INTERVIEW_RESPONSE",
    "EXCEL",
]

AUTO_GRADABLE_EXERCISE_TYPES: frozenset[str] = frozenset({"MULTIPLE_CHOICE", "TRUE_FALSE", "SHORT_ANSWER"})


class SqlHiddenTestSpec(BaseModel):
    """One extra, exercise-authored edge-case check beyond the automatic
    full-result comparison against `sql_solution_query`. `query` must return
    `key_columns` leading columns plus one trailing expected-value column;
    the evaluator looks up matching rows in the *student's* result by key
    and compares the trailing value — see app/sql/evaluation.py."""

    name: str
    query: str
    key_columns: int = Field(default=1, ge=1)


class PythonHiddenTestSpec(BaseModel):
    """One extra, exercise-authored edge-case check beyond the automatic
    comparison of `python_result_variable` against `python_solution_code`'s
    own result. `code` is a Python snippet executed in the *student's own*
    kernel namespace (so it can reference their variables, including
    `python_result_variable`, plus anything else they defined) — it passes
    if it runs without raising (typically via `assert`) and fails otherwise,
    with the exception's message surfaced as feedback. See
    app/python_lab/evaluation.py."""

    name: str
    code: str


class ExcelSheetSpec(BaseModel):
    """One sheet of an Excel exercise's starter or solution workbook (Phase
    9) — `cells` maps a cell ref ("A1") to either a literal ("42"/"Widget")
    or a formula ("=SUM(B2:B10)"), evaluated for real by
    app/excel_lab/formula_engine.py."""

    name: str
    cells: dict[str, str] = Field(default_factory=dict)


class RubricCriterion(BaseModel):
    """One self-assessed evaluation criterion for a rubric-scored exercise
    (spec section 46) — see app.services.grading.grade()."""

    criterion: str
    points: int = Field(gt=0)


class ExerciseContentFile(BaseModel):
    slug: str
    lesson_slug: str | None = None
    skill: str | None = None
    dataset: str | None = None
    title: str
    description: str
    exercise_type: ExerciseTypeLiteral
    difficulty: DifficultyLiteral
    points: int = Field(gt=0)
    tags: list[str] = Field(default_factory=list)
    prompt: str
    choices: list[str] | None = None
    correct_answer: str | None = None
    hints: list[str] = Field(default_factory=list)
    solution: str | None = None
    explanation: str

    # --- SQL exercises only (exercise_type == "SQL") ---
    business_context: str | None = None
    sql_tables: list[str] = Field(
        default_factory=list
    )  # tables to surface in the schema explorer; empty = all
    sql_starter_query: str | None = None
    sql_solution_query: str | None = None
    sql_row_order_matters: bool = False
    sql_numeric_tolerance: float = 0.01
    sql_hidden_tests: list[SqlHiddenTestSpec] = Field(default_factory=list)

    # --- Python exercises only (exercise_type == "PYTHON") ---
    python_datasets: list[str] = Field(
        default_factory=list
    )  # dataset file labels (e.g. "orders") to pre-load as DataFrames; empty = all files in `dataset`
    python_starter_code: str | None = None
    python_solution_code: str | None = None
    python_result_variable: str = "result"  # the variable name both student and solution code must define
    python_row_order_matters: bool = False
    python_numeric_tolerance: float = 1e-6
    python_hidden_tests: list[PythonHiddenTestSpec] = Field(default_factory=list)

    # --- dbt exercises only (exercise_type == "DBT") ---
    # Graded by REAL execution, not text matching: the submitted SQL is
    # written to dbt/models/exercises/<dbt_model_name>.sql in the real dbt
    # project, `dbt build --select <dbt_model_name>` actually runs, and the
    # score comes from whether the model built and its tests passed — see
    # app/services/dbt_exercise_service.py.
    dbt_model_name: str | None = None
    dbt_starter_sql: str | None = None
    # The `columns:` block (and anything else) to nest under this model in a
    # generated schema.yml — e.g. "columns:\n  - name: order_id\n    tests: [unique, not_null]".
    # Never sent to the client as a spec to satisfy; it's what actually gets
    # tested against the student's real, executed model.
    dbt_schema_yml: str | None = None

    # --- Excel exercises only (exercise_type == "EXCEL", Phase 9) ---
    # Graded by REAL formula evaluation (app/excel_lab/formula_engine.py),
    # never by comparing formula text. Each sheet's `cells` maps a cell ref
    # ("A1") to either a literal ("42"/"Widget") or a formula ("=SUM(B2:B10)").
    # `excel_check_cells` (e.g. ["Summary!D2"]) are the only cells actually
    # compared between the student's and the solution's workbook — a student
    # is free to structure any helper columns/formulas they like elsewhere.
    excel_starter_sheets: list[ExcelSheetSpec] = Field(default_factory=list)
    excel_solution_sheets: list[ExcelSheetSpec] = Field(default_factory=list)
    excel_check_cells: list[str] = Field(default_factory=list)

    # --- Case-study / rubric-scored exercises (any exercise_type) ---
    # `business_context` (declared above) doubles as the case's business
    # framing; these add the rest of spec section 44's case shape. `rubric`
    # is shown to the learner *before* they answer (it's evaluation
    # guidance, not the solution) and is what powers self-assessed rubric
    # scoring in app.services.grading — see that module.
    stakeholder: str | None = None
    constraints: list[str] = Field(default_factory=list)
    expected_deliverables: list[str] = Field(default_factory=list)
    rubric: list[RubricCriterion] = Field(default_factory=list)

    source_path: str = ""


# ---------------------------------------------------------------------------
# Case Study / Project content files (Phase 8)
# ---------------------------------------------------------------------------

CaseCategoryLiteral = Literal[
    "BUSINESS_ANALYTICS",
    "PRODUCT_ANALYTICS",
    "CUSTOMER_ANALYTICS",
    "MARKETING_ANALYTICS",
    "OPERATIONS",
    "EXPERIMENTATION",
    "DATA_QUALITY",
    "DATA_ARCHITECTURE",
]
CaseDifficultyLiteral = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"]
CaseStageLiteral = Literal[
    "UNDERSTAND",
    "CLARIFY",
    "FRAME",
    "EXPLORE",
    "ANALYZE",
    "VALIDATE",
    "INSIGHTS",
    "RECOMMEND",
    "COMMUNICATE",
    "SUBMIT",
]


class RubricCategory(BaseModel):
    """One weighted category within a Case/ProjectTemplate rubric (spec
    section 22) — e.g. `{category: "Problem Framing", weight: 15, criteria:
    [...]}`. A category's own score is the checked-points/total-points
    percentage among its own `criteria` (reusing `RubricCriterion` exactly
    as Phase 6's flat, single-category rubric does); the overall score is
    each category's percentage weighted by `weight`. Weights across all of
    a case's categories should sum to 100 (checked by validate.py, not
    enforced here — a partial rubric is a content bug worth surfacing, not
    a silently-renormalized one)."""

    category: str
    weight: float = Field(gt=0, le=100)
    criteria: list[RubricCriterion] = Field(min_length=1)
    # When true, this category's score is computed objectively from whether
    # `required_exercise_slugs` were actually passed (spec section 23 — "use
    # actual execution/testing where possible") instead of the learner's own
    # rubric self-assessment. Usually just the "Technical Analysis" category.
    is_technical: bool = False


class MilestoneSpec(BaseModel):
    """One milestone template within a ProjectTemplate (spec section 31) —
    instantiated into a real `ProjectMilestone` row per project."""

    title: str
    description: str | None = None


class ReferenceSolutionSpec(BaseModel):
    """The hidden reference analysis for a Case (spec section 25) — never
    sent to the client until the attempt is submitted/completed (see
    app/services/case_service.py)."""

    summary: str
    key_insights: list[str] = Field(default_factory=list)
    recommendation: str | None = None
    acceptable_alternatives: list[str] = Field(default_factory=list)


class CaseContentFile(BaseModel):
    """content/cases/<slug>.yaml — a real-world, ambiguous business-problem
    case study (Phase 8). Synced into a `Case` row exactly like Lesson/
    Exercise (see app/content/sync.py); `rubric`/`hints`/
    `clarification_guidance`/`reference_solution` are content the API only
    serves after the learner has earned it (submitted, or explicitly asked
    for a hint) — see app/schemas/case.py's public-vs-full schema split."""

    slug: str
    title: str
    category: CaseCategoryLiteral
    difficulty: CaseDifficultyLiteral
    estimated_minutes: int = Field(gt=0)

    company_context: str | None = None
    stakeholder_name: str
    stakeholder_role: str
    problem_statement: str
    business_context: str | None = None
    objective: str
    initial_information: str | None = None

    constraints: list[str] = Field(default_factory=list)
    available_datasets: list[str] = Field(default_factory=list)  # not all are necessarily relevant
    expected_deliverables: list[str] = Field(default_factory=list)
    learning_objectives: list[str] = Field(min_length=1)
    stages: list[CaseStageLiteral] = Field(default_factory=list)  # cases can skip stages
    required_exercise_slugs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    clarification_guidance: list[str] = Field(default_factory=list)
    rubric: list[RubricCategory] = Field(min_length=1)
    hints: list[str] = Field(default_factory=list)
    reference_solution: ReferenceSolutionSpec

    version: int = Field(default=1, ge=1)
    source_path: str = ""


class ProjectTemplateContentFile(BaseModel):
    """content/projects/<slug>.yaml — a substantial, multi-milestone project
    scenario (Phase 8, spec sections 29-30, 57). Synced into a
    `ProjectTemplate` row; starting one instantiates a `Project` plus its
    `ProjectMilestone` rows from `milestones`."""

    slug: str
    title: str
    category: CaseCategoryLiteral
    business_context: str | None = None
    objective: str
    requirements: list[str] = Field(default_factory=list)
    suggested_datasets: list[str] = Field(default_factory=list)
    milestones: list[MilestoneSpec] = Field(min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    rubric: list[RubricCategory] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    estimated_hours: float | None = Field(default=None, gt=0)
    tags: list[str] = Field(default_factory=list)

    version: int = Field(default=1, ge=1)
    source_path: str = ""


# ---------------------------------------------------------------------------
# Interview content files (Phase 9)
# ---------------------------------------------------------------------------

InterviewQuestionTypeLiteral = Literal[
    "SQL",
    "PYTHON",
    "EXCEL",
    "STATISTICS",
    "AB_TESTING",
    "PRODUCT_ANALYTICS",
    "BUSINESS_ANALYTICS",
    "DATA_INTERPRETATION",
    "DATA_VISUALIZATION",
    "DATA_MODELING",
    "DATA_WAREHOUSING",
    "DBT",
    "DATA_ENGINEERING",
    "BEHAVIORAL",
]


class InterviewQuestionContentFile(BaseModel):
    """content/interview/questions/<slug>.yaml — a thin wrapper adding
    interview-specific metadata (time limit, follow-ups, company archetype
    tags) around an EXISTING Exercise, rather than a parallel question
    format. `exercise_slug` may point at any already-authored exercise
    (Phase 2-8) or a newly-authored one written specifically for this
    phase — the wrapper file never duplicates the exercise's own prompt/
    hints/solution/grading, only decides how it's used inside an interview."""

    slug: str
    exercise_slug: str
    interview_type: InterviewQuestionTypeLiteral
    time_limit_seconds: int | None = Field(default=None, gt=0)
    follow_up_slugs: list[str] = Field(default_factory=list)  # other InterviewQuestion slugs, asked after this one
    company_archetypes: list[str] = Field(default_factory=list)  # e.g. "product_analytics", "business_analyst"

    version: int = Field(default=1, ge=1)
    source_path: str = ""


class InterviewSectionSpec(BaseModel):
    """One timed round within an InterviewTemplate (spec section 32)."""

    interview_type: InterviewQuestionTypeLiteral | Literal["CASE_STUDY"]
    title: str
    duration_minutes: int = Field(gt=0)
    question_count: int = Field(default=1, gt=0)
    difficulty: DifficultyLiteral | None = None  # None = any difficulty


class InterviewTemplateContentFile(BaseModel):
    """content/interview/templates/<slug>.yaml — a configurable mock/company-
    style interview structure (spec sections 32, 46): an ordered list of
    timed sections plus the scoring rubric's category weights (spec section
    37 — must sum to 100; different templates may weight differently, e.g.
    a Business Analyst template can weight Business Understanding higher
    than a Product Analytics one)."""

    slug: str
    title: str
    target_profile: str
    description: str | None = None
    sections: list[InterviewSectionSpec] = Field(min_length=1)
    rubric_weights: dict[str, float] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)

    version: int = Field(default=1, ge=1)
    source_path: str = ""


# ---------------------------------------------------------------------------
# Career content files (Phase 11)
# ---------------------------------------------------------------------------

TargetRoleCategoryLiteral = Literal[
    "DATA_ANALYST",
    "PRODUCT_ANALYST",
    "BUSINESS_ANALYST",
    "BI_ANALYST",
    "MARKETING_ANALYST",
    "ANALYTICS_ENGINEER_ENTRY",
    "ANALYTICS_ENGINEER_INTERMEDIATE",
]


class RoleTemplateContentFile(BaseModel):
    """content/career/role_templates/<slug>.yaml — a generic role template
    (spec section 4) identifying the common core vs. role-specific skills
    for a title, without claiming to represent every employer's exact
    requirements. Skill slugs referenced here must already exist in
    database/seeds/skills.yaml (checked by validate.py), never invented."""

    slug: str
    title: str
    category: TargetRoleCategoryLiteral
    description: str | None = None
    core_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    typical_responsibilities: list[str] = Field(default_factory=list)

    version: int = Field(default=1, ge=1)
    source_path: str = ""
