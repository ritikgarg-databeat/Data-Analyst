from enum import StrEnum


class UserRole(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class AccountStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class DifficultyLevel(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class LessonContentType(StrEnum):
    READING = "READING"
    VIDEO = "VIDEO"
    INTERACTIVE = "INTERACTIVE"
    EXERCISE = "EXERCISE"
    QUIZ = "QUIZ"


class LessonProgressStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ExerciseType(StrEnum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    CODE = "CODE"
    SQL = "SQL"
    PYTHON = "PYTHON"
    DBT = "DBT"
    BUSINESS_REASONING = "BUSINESS_REASONING"
    DATA_INTERPRETATION = "DATA_INTERPRETATION"
    MODELING = "MODELING"
    INTERVIEW_RESPONSE = "INTERVIEW_RESPONSE"
    EXCEL = "EXCEL"  # Phase 9 — real formula-evaluation grading, see app/excel_lab/


# Exercise types gradable purely from content-file data (no execution engine
# needed) — see app/services/grading.py. Everything else is recorded as
# SUBMITTED pending a future execution/AI-graded engine (Phase 3/4/11).
AUTO_GRADABLE_EXERCISE_TYPES: frozenset[ExerciseType] = frozenset(
    {ExerciseType.MULTIPLE_CHOICE, ExerciseType.TRUE_FALSE, ExerciseType.SHORT_ANSWER}
)


class ExerciseAttemptStatus(StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"  # recorded but not auto-graded (no execution engine yet)
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


class PythonRuntimeStatus(StrEnum):
    STARTING = "STARTING"
    READY = "READY"
    BUSY = "BUSY"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


class AssessmentRetryPolicy(StrEnum):
    UNLIMITED = "UNLIMITED"
    LIMITED = "LIMITED"


class AssessmentAttemptStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"


class CompletionRuleType(StrEnum):
    READING_PERCENT = "reading_percent"
    EXERCISE_SCORE = "exercise_score"
    ASSESSMENT_SCORE = "assessment_score"


# 0-39 Beginner / 40-59 Developing / 60-74 Intermediate / 75-89 Strong / 90-100 Mastered.
# Thresholds are deliberately centralized here (not scattered across services)
# so they stay a single, easy-to-tune configuration point.
class MasteryLevel(StrEnum):
    BEGINNER = "BEGINNER"
    DEVELOPING = "DEVELOPING"
    INTERMEDIATE = "INTERMEDIATE"
    STRONG = "STRONG"
    MASTERED = "MASTERED"


MASTERY_LEVEL_THRESHOLDS: list[tuple[float, MasteryLevel]] = [
    (90, MasteryLevel.MASTERED),
    (75, MasteryLevel.STRONG),
    (60, MasteryLevel.INTERMEDIATE),
    (40, MasteryLevel.DEVELOPING),
    (0, MasteryLevel.BEGINNER),
]


def mastery_level_for_score(score: float) -> MasteryLevel:
    for threshold, level in MASTERY_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return MasteryLevel.BEGINNER


class DatasetSourceType(StrEnum):
    LOCAL = "LOCAL"
    KAGGLE = "KAGGLE"
    GENERATED = "GENERATED"
    PUBLIC_API = "PUBLIC_API"
    OTHER = "OTHER"


# AVAILABLE is unused today (nothing produces it) but kept per the Phase 5 spec
# as the natural "not yet imported" state for a future catalog-of-known-but-
# not-yet-downloaded-datasets feature — an intentional extension point.
class DatasetStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    IMPORTING = "IMPORTING"
    PROFILING = "PROFILING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class DataModelKind(StrEnum):
    """What a saved DataModel graph represents — the same node/edge tables
    back all three (spec section 60), since "a labeled graph of boxes and
    arrows" is the shared shape underneath a dimensional model, an
    architecture diagram, and a pipeline."""

    DIMENSIONAL = "DIMENSIONAL"
    ARCHITECTURE = "ARCHITECTURE"
    PIPELINE = "PIPELINE"


class DataModelTableType(StrEnum):
    """Node classification — meaning depends on the parent DataModel.model_kind:
    FACT/DIMENSION/BRIDGE/OTHER for DIMENSIONAL; the rest for
    ARCHITECTURE/PIPELINE node types."""

    FACT = "FACT"
    DIMENSION = "DIMENSION"
    BRIDGE = "BRIDGE"
    SOURCE = "SOURCE"
    STORAGE = "STORAGE"
    WAREHOUSE = "WAREHOUSE"
    TRANSFORM = "TRANSFORM"
    SERVICE = "SERVICE"
    STREAM = "STREAM"
    BI = "BI"
    OTHER = "OTHER"


class DataModelRelationshipType(StrEnum):
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"
    FLOW = "FLOW"  # architecture: data moves from -> to
    DEPENDS_ON = "DEPENDS_ON"  # pipeline: to depends on from completing first


class DataQualityRuleType(StrEnum):
    NOT_NULL = "NOT_NULL"
    UNIQUE = "UNIQUE"
    ACCEPTED_VALUES = "ACCEPTED_VALUES"
    RELATIONSHIP = "RELATIONSHIP"
    MIN_MAX = "MIN_MAX"
    FRESHNESS = "FRESHNESS"
    ROW_COUNT = "ROW_COUNT"


class DataQualityStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class DbtCommand(StrEnum):
    RUN = "run"
    TEST = "test"
    BUILD = "build"
    COMPILE = "compile"
    DOCS_GENERATE = "docs generate"


class DbtRunStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ERROR = "ERROR"


class SkillCategory(StrEnum):
    SQL = "SQL"
    PYTHON = "PYTHON"
    STATISTICS = "STATISTICS"
    EXCEL = "EXCEL"
    DATA_VISUALIZATION = "DATA_VISUALIZATION"
    BUSINESS_ANALYTICS = "BUSINESS_ANALYTICS"
    PRODUCT_ANALYTICS = "PRODUCT_ANALYTICS"
    DATA_ENGINEERING = "DATA_ENGINEERING"
    DATA_WAREHOUSING = "DATA_WAREHOUSING"
    DATA_MODELING = "DATA_MODELING"
    MACHINE_LEARNING = "MACHINE_LEARNING"
    INTERVIEW_READINESS = "INTERVIEW_READINESS"


# Kept in sync with packages/shared/src/constants.ts SKILL_CATEGORY_LABELS.
SKILL_CATEGORY_LABELS: dict[SkillCategory, str] = {
    SkillCategory.SQL: "SQL",
    SkillCategory.PYTHON: "Python",
    SkillCategory.STATISTICS: "Statistics",
    SkillCategory.EXCEL: "Excel",
    SkillCategory.DATA_VISUALIZATION: "Data Visualization",
    SkillCategory.BUSINESS_ANALYTICS: "Business Analytics",
    SkillCategory.PRODUCT_ANALYTICS: "Product Analytics",
    SkillCategory.DATA_ENGINEERING: "Data Engineering",
    SkillCategory.DATA_WAREHOUSING: "Data Warehousing",
    SkillCategory.DATA_MODELING: "Data Modeling",
    SkillCategory.MACHINE_LEARNING: "Machine Learning",
    SkillCategory.INTERVIEW_READINESS: "Interview Readiness",
}


class CaseCategory(StrEnum):
    """The business domain a case study is framed around (Phase 8, spec
    section 3) — deliberately separate from SkillCategory: a single case
    typically exercises several skills (SQL + Python + business reasoning)
    but belongs to exactly one narrative category."""

    BUSINESS_ANALYTICS = "BUSINESS_ANALYTICS"
    PRODUCT_ANALYTICS = "PRODUCT_ANALYTICS"
    CUSTOMER_ANALYTICS = "CUSTOMER_ANALYTICS"
    MARKETING_ANALYTICS = "MARKETING_ANALYTICS"
    OPERATIONS = "OPERATIONS"
    EXPERIMENTATION = "EXPERIMENTATION"
    DATA_QUALITY = "DATA_QUALITY"
    DATA_ARCHITECTURE = "DATA_ARCHITECTURE"


class CaseDifficulty(StrEnum):
    """A separate scale from the shared DifficultyLevel (BEGINNER/INTERMEDIATE/
    ADVANCED) used by Lesson/Exercise/Module — cases add a 4th "almost no
    guidance" tier (spec section 27) that wouldn't make sense to retrofit
    onto every other content type in the platform."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class CaseAttemptStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    COMPLETED = "COMPLETED"


class CaseStage(StrEnum):
    """The case's own stage tracker (spec section 14) — cases can skip
    stages where appropriate, so this is a label on `CaseAttempt.current_stage`,
    not a hard state machine that rejects out-of-order progress."""

    UNDERSTAND = "UNDERSTAND"
    CLARIFY = "CLARIFY"
    FRAME = "FRAME"
    EXPLORE = "EXPLORE"
    ANALYZE = "ANALYZE"
    VALIDATE = "VALIDATE"
    INSIGHTS = "INSIGHTS"
    RECOMMEND = "RECOMMEND"
    COMMUNICATE = "COMMUNICATE"
    SUBMIT = "SUBMIT"


class HypothesisStatus(StrEnum):
    UNCHECKED = "UNCHECKED"
    INVESTIGATING = "INVESTIGATING"
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class FindingConfidence(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceType(StrEnum):
    """What a piece of evidence points back at (spec sections 15-16, 52) —
    always paired with a denormalized snapshot (see CaseEvidence's
    docstring), so a finding stays meaningful even if the referenced row is
    later deleted (spec section 60's data-integrity requirement)."""

    SQL_QUERY = "SQL_QUERY"
    PYTHON_EXECUTION = "PYTHON_EXECUTION"
    CHART = "CHART"
    STATISTIC = "STATISTIC"
    DATASET = "DATASET"
    DATA_MODEL = "DATA_MODEL"
    DBT_MODEL = "DBT_MODEL"


class ProjectArtifactType(StrEnum):
    """What a project artifact links back at (spec section 33) — SQL/Python
    files, notebooks, charts, and structured outputs are all just links back
    to already-real rows elsewhere (SqlQueryHistory/PythonExecution/Chart/...)
    plus a free-text note/label; NOTE covers markdown/diagram/CSV/JSON write-ups
    that don't correspond to any existing entity."""

    SQL_QUERY = "SQL_QUERY"
    PYTHON_EXECUTION = "PYTHON_EXECUTION"
    CHART = "CHART"
    DATA_MODEL = "DATA_MODEL"
    DBT_MODEL = "DBT_MODEL"
    NOTE = "NOTE"


class InterviewQuestionType(StrEnum):
    """The interview-round domain a question belongs to (Phase 9, spec
    section 5) — orthogonal to `ExerciseType` (the grading *mechanic*: SQL/
    PYTHON/MULTIPLE_CHOICE/etc). E.g. a Statistics interview question is
    mechanically a SHORT_ANSWER or MULTIPLE_CHOICE Exercise; its
    InterviewQuestionType is STATISTICS. CASE_STUDY is deliberately absent —
    a "Case Study" interview round pulls directly from the existing Phase 8
    Case/CaseAttempt system (filtered to interview-tagged cases), not from
    InterviewQuestion, to avoid a third parallel case format."""

    SQL = "SQL"
    PYTHON = "PYTHON"
    EXCEL = "EXCEL"
    STATISTICS = "STATISTICS"
    AB_TESTING = "AB_TESTING"
    PRODUCT_ANALYTICS = "PRODUCT_ANALYTICS"
    BUSINESS_ANALYTICS = "BUSINESS_ANALYTICS"
    DATA_INTERPRETATION = "DATA_INTERPRETATION"
    DATA_VISUALIZATION = "DATA_VISUALIZATION"
    DATA_MODELING = "DATA_MODELING"
    DATA_WAREHOUSING = "DATA_WAREHOUSING"
    DBT = "DBT"
    DATA_ENGINEERING = "DATA_ENGINEERING"
    BEHAVIORAL = "BEHAVIORAL"


class InterviewMode(StrEnum):
    PRACTICE = "PRACTICE"
    TIMED = "TIMED"
    MOCK = "MOCK"
    COMPANY_STYLE = "COMPANY_STYLE"
    WEAKNESS_DRILL = "WEAKNESS_DRILL"
    FINAL_READINESS = "FINAL_READINESS"


class InterviewStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class InterviewTargetType(StrEnum):
    """What an InterviewBookmark/InterviewNote points at — a plain slug/id
    lookup by type rather than a separate join table per target, since a
    bookmark/note is a lightweight, single-row concern (mirrors EvidenceType's
    reasoning for the same tradeoff)."""

    QUESTION = "QUESTION"
    CASE = "CASE"
    ASSESSMENT = "ASSESSMENT"  # an InterviewTemplate ("company-style assessment")
    INTERVIEW = "INTERVIEW"
    SKILL = "SKILL"


# --- AI Layer (Phase 10) ---
# Every engine above this line (case_engine, interview_engine, stats_engine,
# experimentation_engine, dataset_hub, dbt_lab, data_modeling) is fully
# deterministic — no LLM call anywhere. This section's enums back the AI
# layer built ON TOP of them: a reasoning/coaching layer that reads their
# real, already-computed outputs and narrates/explains/questions around them,
# never a second, competing scoring system (see app/ai/AUTHORITY.md).


class AIProviderName(StrEnum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    LOCAL = "LOCAL"  # deterministic, template-based fallback — needs no API key


class AIFeature(StrEnum):
    """Which capability a request is invoking — selects the prompt template
    (app/ai/prompts/<feature>/) and is recorded on every AIAuditLog row. The
    six domain-specific coaches named in the spec (Statistics/Experimentation/
    Product Analytics/Business Analytics/Data Modeling/dbt) share ONE
    DOMAIN_COACH feature with the domain carried in AIDomain — a coach is a
    system prompt + a context shape, not a different code path per domain."""

    MENTOR = "MENTOR"
    SQL_TUTOR = "SQL_TUTOR"
    SQL_REVIEW = "SQL_REVIEW"
    SQL_DEBUG = "SQL_DEBUG"
    SQL_OPTIMIZATION = "SQL_OPTIMIZATION"
    PYTHON_TUTOR = "PYTHON_TUTOR"
    PYTHON_REVIEW = "PYTHON_REVIEW"
    ANALYSIS_REVIEW = "ANALYSIS_REVIEW"
    INSIGHT_REVIEW = "INSIGHT_REVIEW"
    DOMAIN_COACH = "DOMAIN_COACH"
    NL_TO_SQL = "NL_TO_SQL"
    NL_TO_PYTHON = "NL_TO_PYTHON"
    EDA_ASSISTANT = "EDA_ASSISTANT"
    DATA_EXPLORATION = "DATA_EXPLORATION"
    CASE_COACH = "CASE_COACH"
    CASE_INTERVIEWER = "CASE_INTERVIEWER"
    BEHAVIORAL_INTERVIEWER = "BEHAVIORAL_INTERVIEWER"
    INTERVIEW_DEBRIEF = "INTERVIEW_DEBRIEF"
    COMMUNICATION_COACH = "COMMUNICATION_COACH"
    STORYTELLING_COACH = "STORYTELLING_COACH"
    EXEC_SUMMARY = "EXEC_SUMMARY"
    LEARNING_PLANNER = "LEARNING_PLANNER"
    SKILL_DIAGNOSIS = "SKILL_DIAGNOSIS"
    PROJECT_REVIEW = "PROJECT_REVIEW"
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
    JD_EXTRACTION = "JD_EXTRACTION"  # Phase 11 — structured requirement extraction from a pasted/uploaded JD
    RESUME_REVIEW = "RESUME_REVIEW"  # Phase 11 — resume quality/clarity/impact review
    CAREER_COACH = "CAREER_COACH"  # Phase 11 — explains career plan/readiness/weekly review, never invents
    PORTFOLIO_REVIEW = "PORTFOLIO_REVIEW"  # Phase 11 — portfolio quality/presentation feedback


class AIDomain(StrEnum):
    """Only meaningful alongside AIFeature.DOMAIN_COACH."""

    STATISTICS = "STATISTICS"
    EXPERIMENTATION = "EXPERIMENTATION"
    PRODUCT_ANALYTICS = "PRODUCT_ANALYTICS"
    BUSINESS_ANALYTICS = "BUSINESS_ANALYTICS"
    DATA_MODELING = "DATA_MODELING"
    DBT = "DBT"


class AIMode(StrEnum):
    """The persona/stance a request is answered in (spec section 49) — changes
    the system prompt's tone/behavior independently of which AIFeature it is."""

    TUTOR = "TUTOR"
    COACH = "COACH"
    REVIEWER = "REVIEWER"
    INTERVIEWER = "INTERVIEWER"
    ANALYST = "ANALYST"
    EXPLAINER = "EXPLAINER"


class AICaseCoachingMode(StrEnum):
    GUIDED = "GUIDED"
    STANDARD = "STANDARD"
    INTERVIEW = "INTERVIEW"
    STRICT = "STRICT"


class AIClaimType(StrEnum):
    """Hallucination-prevention labels (spec section 17) — every data-specific
    claim an AI response makes must be tagged with exactly one of these."""

    OBSERVED = "OBSERVED"  # directly supported by provided context
    INFERRED = "INFERRED"  # reasonable interpretation of provided context
    HYPOTHESIS = "HYPOTHESIS"  # possible explanation requiring validation
    UNKNOWN = "UNKNOWN"  # not supported by available context


class AIConversationRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


# --- Career Readiness & Job Preparation (Phase 11) ---
# This layer answers "am I ready for a specific role, what are my gaps, and
# how should I prepare" by reading the deterministic engines above
# (MasteryService, ProgressService, InterviewReadinessService) as INPUT
# SIGNALS and adding its own career-specific aggregation/gating on top —
# never a second, competing mastery/interview-score system. AI (Phase 10)
# explains and coaches around these deterministic numbers; it never computes
# them (see app/ai/AUTHORITY.md).


class TargetRoleCategory(StrEnum):
    """A generic Role Template category (spec section 4) — the common shape
    of these titles in the industry, not a claim to represent every
    employer's exact requirements."""

    DATA_ANALYST = "DATA_ANALYST"
    PRODUCT_ANALYST = "PRODUCT_ANALYST"
    BUSINESS_ANALYST = "BUSINESS_ANALYST"
    BI_ANALYST = "BI_ANALYST"
    MARKETING_ANALYST = "MARKETING_ANALYST"
    ANALYTICS_ENGINEER_ENTRY = "ANALYTICS_ENGINEER_ENTRY"
    ANALYTICS_ENGINEER_INTERMEDIATE = "ANALYTICS_ENGINEER_INTERMEDIATE"


class JDSource(StrEnum):
    PASTED = "PASTED"
    UPLOADED = "UPLOADED"


class JDRequirementKind(StrEnum):
    """What an extracted JD requirement IS — orthogonal to
    JDRequirementPriority (how important it is)."""

    SKILL = "SKILL"
    TOOL = "TOOL"
    RESPONSIBILITY = "RESPONSIBILITY"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    DOMAIN_KNOWLEDGE = "DOMAIN_KNOWLEDGE"
    SOFT_SKILL = "SOFT_SKILL"
    BUSINESS_EXPECTATION = "BUSINESS_EXPECTATION"


class JDRequirementPriority(StrEnum):
    MUST_HAVE = "MUST_HAVE"
    STRONGLY_PREFERRED = "STRONGLY_PREFERRED"
    NICE_TO_HAVE = "NICE_TO_HAVE"


class SkillGapSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    MODERATE = "MODERATE"
    MINOR = "MINOR"


class ResumeSource(StrEnum):
    PASTED = "PASTED"
    UPLOADED = "UPLOADED"


class PortfolioItemType(StrEnum):
    PROJECT = "PROJECT"
    CASE_STUDY = "CASE_STUDY"
    CERTIFICATION = "CERTIFICATION"
    ACHIEVEMENT = "ACHIEVEMENT"
    SKILL_HIGHLIGHT = "SKILL_HIGHLIGHT"


class PrivacyLevel(StrEnum):
    """Per-artifact visibility for portfolio content (spec section 20) —
    defaults to PRIVATE everywhere it's used; nothing becomes PORTFOLIO or
    PUBLIC_READY without an explicit user action."""

    PRIVATE = "PRIVATE"
    PORTFOLIO = "PORTFOLIO"
    PUBLIC_READY = "PUBLIC_READY"


class CareerGoalType(StrEnum):
    TARGET_ROLE = "TARGET_ROLE"
    SKILL_MASTERY = "SKILL_MASTERY"
    READINESS_LEVEL = "READINESS_LEVEL"
    PORTFOLIO_COMPLETION = "PORTFOLIO_COMPLETION"
    INTERVIEW_PREP = "INTERVIEW_PREP"
    CUSTOM = "CUSTOM"


class CareerGoalStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class CareerMilestoneType(StrEnum):
    """What triggered a Career Progress Timeline entry — every value is
    written from a real deterministic event elsewhere, never invented."""

    SKILL_LEVEL_UP = "SKILL_LEVEL_UP"
    PROJECT_COMPLETED = "PROJECT_COMPLETED"
    CASE_COMPLETED = "CASE_COMPLETED"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
    ASSESSMENT_PASSED = "ASSESSMENT_PASSED"
    GOAL_COMPLETED = "GOAL_COMPLETED"
    READINESS_LEVEL_UP = "READINESS_LEVEL_UP"
    ACHIEVEMENT_EARNED = "ACHIEVEMENT_EARNED"


class CareerEvidenceLevel(StrEnum):
    """5-level evidence-based mastery (spec section 22) — distinct from
    MasteryLevel (score-based): this is about HOW a skill has been
    demonstrated (practice count / applied in a project / interview
    performance), never computed from a single test."""

    LEARNED = "LEARNED"
    PRACTICED = "PRACTICED"
    APPLIED = "APPLIED"
    INTERVIEW_READY = "INTERVIEW_READY"
    DEMONSTRATED = "DEMONSTRATED"


class CareerRubricDimension(StrEnum):
    """The 8 named dimensions of the Career Readiness Rubric (spec section
    23) — deliberately NOT the same as SkillCategory (12 values, with no
    Communication/Interview/Portfolio dimension); see
    app/services/career_readiness_service.py for the mapping."""

    TECHNICAL = "TECHNICAL"
    ANALYTICAL = "ANALYTICAL"
    BUSINESS = "BUSINESS"
    PRODUCT = "PRODUCT"
    DATA_ENGINEERING_AWARENESS = "DATA_ENGINEERING_AWARENESS"
    COMMUNICATION = "COMMUNICATION"
    INTERVIEW = "INTERVIEW"
    PORTFOLIO = "PORTFOLIO"


class CareerReadinessLevel(StrEnum):
    FOUNDATION = "FOUNDATION"
    DEVELOPING = "DEVELOPING"
    INTERMEDIATE = "INTERMEDIATE"
    INTERVIEW_READY = "INTERVIEW_READY"
    STRONG_CANDIDATE = "STRONG_CANDIDATE"
    EXCEPTIONAL = "EXCEPTIONAL"


class BehavioralStoryCategory(StrEnum):
    """Matches the real tag taxonomy already used across
    content/exercises/behavioral/*.yaml (Phase 9) rather than a new,
    parallel set of category names."""

    AMBIGUITY = "AMBIGUITY"
    COMMUNICATION = "COMMUNICATION"
    CONFLICT = "CONFLICT"
    DEADLINES = "DEADLINES"
    DISAGREEMENT = "DISAGREEMENT"
    WORKING_WITH_ENGINEERS = "WORKING_WITH_ENGINEERS"
    FAILURE = "FAILURE"
    INCOMPLETE_DATA = "INCOMPLETE_DATA"
    INFLUENCING = "INFLUENCING"
    OWNERSHIP = "OWNERSHIP"
    PRIORITIZATION = "PRIORITIZATION"
    STAKEHOLDER_MANAGEMENT = "STAKEHOLDER_MANAGEMENT"


class JobPrepStatus(StrEnum):
    SAVED = "SAVED"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    ARCHIVED = "ARCHIVED"
