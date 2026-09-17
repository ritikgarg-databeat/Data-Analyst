"""AI Communication Coach / Data Storytelling Coach / Executive Communication
Coach (spec sections 31, 57-58)."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AIExecSummaryResult, AIReviewResult

COMMUNICATION_COACH = PromptTemplate(
    feature=AIFeature.COMMUNICATION_COACH,
    version="1.0",
    purpose="Review answers for clarity, structure, conciseness, evidence, business language, "
    "jargon, directness (spec section 31). Provide a better version only when useful, not always.",
    input_schema={"text": "the learner's written answer/response", "audience": "str|None"},
    output_schema=AIReviewResult,
    default_mode=AIMode.REVIEWER,
    instructions="""Review this written communication for clarity, structure, conciseness, whether \
it's backed by evidence, business (not overly technical) language, unnecessary jargon, and \
directness. Put a rewritten version in `suggestions` ONLY if a rewrite would genuinely help (a \
structurally sound answer doesn't need one) — say explicitly in `summary` when you're intentionally \
not providing one because the original is already clear.""",
)

STORYTELLING_COACH = PromptTemplate(
    feature=AIFeature.STORYTELLING_COACH,
    version="1.0",
    purpose="Data Storytelling Coach (spec section 57): story structure, chart choice, headline, "
    "key takeaway, audience, business action. Teaches 'don't make the audience find the insight'.",
    input_schema={"findings_text": "the learner's findings/narrative", "chart_description": "str|None"},
    output_schema=AIReviewResult,
    default_mode=AIMode.COACH,
    instructions="""Coach this analysis's storytelling. Assess: does the story lead with the \
insight, or make the reader hunt for it; is the chart choice (if described) suited to the point \
being made; is there a clear headline and key takeaway; is the framing right for the stated \
audience; does it end in a business action, not just an observation. Teach the core principle \
explicitly where it's missing: the reader should never have to find the insight themselves.""",
)

EXEC_SUMMARY = PromptTemplate(
    feature=AIFeature.EXEC_SUMMARY,
    version="1.0",
    purpose="Executive Communication Coach (spec section 58): turn an analysis into a 5-line "
    "executive summary (what happened / why / impact / recommendation / next step).",
    input_schema={"analysis_text": "the learner's full analysis/findings text"},
    output_schema=AIExecSummaryResult,
    default_mode=AIMode.EXPLAINER,
    instructions="""Turn the given analysis into a 5-line executive summary: what happened, why, \
the business impact, the recommendation, and the next step. Use ONLY what's stated in the given \
analysis text — if the analysis doesn't actually state a cause, impact, or recommendation, say so \
in that field (e.g. "Not stated in the analysis — this needs a recommendation before it's ready to \
send") rather than inventing one. This is AI-generated communication, not a validated fact — the \
caller is responsible for showing it as a draft, not as an established finding.""",
)
