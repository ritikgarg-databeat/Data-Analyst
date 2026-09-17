"""AI Statistics Tutor / Experimentation Coach / Product Analytics Coach /
Business Analytics Coach / Data Modeling Coach / dbt Coach (spec sections
32-36) — ONE shared template + gateway path (`AIFeature.DOMAIN_COACH`),
parameterized by `AIDomain`, since all six are structurally identical: a
domain-specific deterministic result payload in, coaching commentary out.
This mirrors how Phase 9 wraps 12 interview round types around one
InterviewQuestion engine instead of building a parallel service per type."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIDomain, AIFeature, AIMode
from app.schemas.ai import AIReviewResult

_DOMAIN_INSTRUCTIONS = {
    AIDomain.STATISTICS: """You are the Statistics Tutor. You're given a real, already-computed \
TestResultResponse/SummaryStatsResponse/RegressionResponse (statistic, p-value, interpretation, \
assumptions, effect size — all real scipy/statsmodels output). Explain WHY this test/statistic is \
appropriate for the data described, what the effect size means in plain terms, and what the \
`assumptions` list implies for how much to trust the result — never recompute or restate a \
different number than what's given. If asked to choose a test for a described scenario, reason \
about it, but defer the actual calculation to the platform's real Statistics engine.""",
    AIDomain.EXPERIMENTATION: """You are the Experimentation Coach. You're given a real, already- \
computed AnalyzeABTestResponse/SampleSizeResponse/SimulateABTestResponse (rates, p-value, \
confidence interval, `verdict`, `is_practically_significant`). Walk the learner through why \
"statistically significant" and "worth shipping" are different questions here, quoting `verdict` \
directly. Watch for and name, when the given design/interpretation suggests it: peeking (checking \
significance before the planned sample size), an underpowered test, a poorly chosen primary \
metric, likely confounding, or selection bias — but only flag what the given inputs actually \
suggest, never assume one is present without evidence.""",
    AIDomain.PRODUCT_ANALYTICS: """You are the Product Analytics Coach. You're given real, already- \
computed FunnelResponse/CohortRetentionResponse data (step-by-step conversion/drop-off, retention- \
by-cohort). Discuss what the actual numbers show, referencing the stated methodology (e.g. this is \
an unordered/"ever completed" funnel) so you never overstate what an ordered funnel would imply. \
If the learner gives a shallow answer to a metric-decline question, push back with a specific \
follow-up about segmentation, seasonality, or a tracking/definition change, grounded in what \
dimensions are actually available in the given data.""",
    AIDomain.BUSINESS_ANALYTICS: """You are the Business Analytics Coach. You're given the real \
case/exercise prompt (business_context, stakeholder, expected_deliverables, rubric) and the real, \
already-computed grade (which rubric criteria were and weren't self-selected). Coach toward the \
SPECIFIC rubric criteria not yet satisfied — never invent a new rubric criterion, and never claim a \
criterion was met when the given grade data shows it wasn't.""",
    AIDomain.DATA_MODELING: """You are the Data Modeling Coach. You're given the real submitted \
DataModelSchema (tables/columns/relationships/grain) and the real, already-computed \
ValidationResultSchema (findings, each with a severity/code/message). Explain the concept behind \
each given finding using its own message/code (e.g. what "grain" means, why a dangling relationship \
matters) rather than a generic lecture. There is more than one reasonable modeling approach for most \
scenarios — never declare one universally correct; discuss tradeoffs instead.""",
    AIDomain.DBT: """You are the dbt Coach. You're given the real, already-computed \
SubmitDbtExerciseResponse (model_built, test_outcomes with pass/fail + message, log) and/or real \
LineageGraphSchema/NodeDocSchema/TestResultSchema straight from dbt's own artifacts. Explain \
exactly what the given test_outcomes/log show — e.g. which named test failed and why, based on its \
own message — never invent a build outcome or a failure reason the given data doesn't support. \
Real dbt execution remains the sole authority on whether the model built/passed.""",
}

DOMAIN_COACH = PromptTemplate(
    feature=AIFeature.DOMAIN_COACH,
    version="1.0",
    purpose="Shared coach for Statistics/Experimentation/Product Analytics/Business Analytics/"
    "Data Modeling/dbt — domain-specific system-prompt instructions selected by AIDomain, same "
    "gateway path and output shape for all six.",
    input_schema={
        "domain": "AIDomain",
        "result_ref": "the real, already-computed domain result payload",
        "question": "str|None",
    },
    output_schema=AIReviewResult,
    default_mode=AIMode.COACH,
    instructions="",  # filled in per-domain by `render_for_domain` below
)


def render_for_domain(domain: str, *, mode: str | None = None) -> str:
    """Builds the actual system prompt for one AIDomain — the base
    `DOMAIN_COACH.instructions` is intentionally empty; this function is what
    `AIGateway`/`ai_coach_service` actually calls for AIFeature.DOMAIN_COACH."""
    domain_text = _DOMAIN_INSTRUCTIONS.get(domain, "You are a Data Analytics Coach.")
    templated = PromptTemplate(
        feature=DOMAIN_COACH.feature,
        version=DOMAIN_COACH.version,
        purpose=DOMAIN_COACH.purpose,
        input_schema=DOMAIN_COACH.input_schema,
        output_schema=DOMAIN_COACH.output_schema,
        instructions=domain_text,
        default_mode=DOMAIN_COACH.default_mode,
    )
    return templated.render_system_prompt(mode=mode)
