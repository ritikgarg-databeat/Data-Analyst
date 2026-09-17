"""Data Analysis Review / Insight Reviewer / AI EDA Assistant / AI Data
Exploration (spec sections 15-17, 22-23)."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AIEdaResult, AIInsightReviewResult, AIReviewResult

ANALYSIS_REVIEW = PromptTemplate(
    feature=AIFeature.ANALYSIS_REVIEW,
    version="1.0",
    purpose="Review My Analysis (spec section 15): whether the analysis answers the business "
    "question, missing analyses, possible bias, segmentation opportunities, statistical concerns, "
    "business interpretation.",
    input_schema={
        "business_question": "str",
        "dataset_metadata": "real schema/profile",
        "code": "str|None",
        "output": "str|None",
        "findings": "str|None",
    },
    output_schema=AIReviewResult,
    default_mode=AIMode.REVIEWER,
    instructions="""Review this analysis against the stated business question. You're given the \
real dataset metadata, the learner's code/output/findings (whatever is available). Assess: does \
the analysis actually answer the question asked, what's missing, any likely bias (e.g. survivorship, \
selection), worthwhile segmentation not yet explored, statistical concerns (sample size, \
confounding, multiple comparisons), and whether the business interpretation drawn is warranted by \
what was actually computed.""",
)

INSIGHT_REVIEW = PromptTemplate(
    feature=AIFeature.INSIGHT_REVIEW,
    version="1.0",
    purpose="Insight Reviewer (spec section 16): evaluate the Observation/Evidence/Impact/"
    "Recommendation structure explicitly, one verdict per part.",
    input_schema={"observation": "str", "evidence": "str", "impact": "str", "recommendation": "str"},
    output_schema=AIInsightReviewResult,
    default_mode=AIMode.REVIEWER,
    instructions="""Evaluate this Observation/Evidence/Impact/Recommendation exactly as a 4-part \
structure. For OBSERVATION: is it actually supported by the stated evidence? For EVIDENCE: is it \
sufficient to support the observation (not just present, but enough)? For IMPACT: is the stated \
business implication a reasonable reading of the observation? For RECOMMENDATION: does it actually \
follow from the evidence, or does it overreach? Give a boolean verdict and a short, specific note \
for each of the four, plus one overall assessment.""",
)

EDA_ASSISTANT = PromptTemplate(
    feature=AIFeature.EDA_ASSISTANT,
    version="1.0",
    purpose="AI EDA Assistant (spec section 23): given a dataset's real profile, what to inspect, "
    "data quality issues, important variables, suggested visualizations/questions/hypotheses — "
    "observed issues kept separate from suggested investigations.",
    input_schema={"dataset_profile": "real DatasetProfileResponse/EdaOverview"},
    output_schema=AIEdaResult,
    default_mode=AIMode.ANALYST,
    instructions="""You're given a dataset's real, already-computed profile (column types, null %, \
distributions, correlations, outliers). Put anything the profile ITSELF already shows (e.g. a \
column with 40% nulls, a heavily skewed distribution) in `observed_issues` — these must be \
traceable to a specific number in the given profile. Put anything that would need further, \
not-yet-run analysis to confirm (e.g. "check whether the nulls correlate with signup date") in \
`suggested_investigations`. Also list what to inspect first, the variables that look most \
important, useful visualizations, good analytical questions, and plausible hypotheses (framed as \
hypotheses, not conclusions).""",
)

DATA_EXPLORATION = PromptTemplate(
    feature=AIFeature.DATA_EXPLORATION,
    version="1.0",
    purpose="Explore with AI (spec section 22): propose questions, useful columns, segmentation, "
    "visualizations, potential anomalies, hypotheses — without claiming findings before analyzing.",
    input_schema={"dataset_profile": "real schema/profile", "user_goal": "str|None"},
    output_schema=AIEdaResult,
    default_mode=AIMode.EXPLAINER,
    instructions="""Propose a data-exploration plan for this real dataset (schema/profile given \
below), optionally guided by the learner's stated goal. You are proposing what to explore, not \
claiming you've already found something — never phrase a suggestion as if it were an already-\
established finding. Use `observed_issues` only for what the given profile already shows; \
everything else the learner would still need to go check belongs in `suggested_investigations`, \
`suggested_questions`, or `potential_hypotheses`.""",
)
