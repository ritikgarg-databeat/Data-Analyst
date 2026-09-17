"""Central `AIFeature -> PromptTemplate` registry. `app/ai/gateway.py` is the
only caller — it never imports an individual prompt module directly, so
adding a new feature never requires touching the Gateway."""

from app.ai.prompts.analysis import ANALYSIS_REVIEW, DATA_EXPLORATION, EDA_ASSISTANT, INSIGHT_REVIEW
from app.ai.prompts.base import PromptTemplate
from app.ai.prompts.behavioral import BEHAVIORAL_INTERVIEWER
from app.ai.prompts.career import CAREER_COACH, JD_EXTRACTION, PORTFOLIO_REVIEW, RESUME_REVIEW
from app.ai.prompts.case_interviewer import CASE_COACH, CASE_INTERVIEWER
from app.ai.prompts.communication import COMMUNICATION_COACH, EXEC_SUMMARY, STORYTELLING_COACH
from app.ai.prompts.domain_coach import DOMAIN_COACH
from app.ai.prompts.interview_debrief import INTERVIEW_DEBRIEF
from app.ai.prompts.knowledge import KNOWLEDGE_SEARCH
from app.ai.prompts.mentor import MENTOR
from app.ai.prompts.planner import LEARNING_PLANNER, SKILL_DIAGNOSIS
from app.ai.prompts.project_review import PROJECT_REVIEW
from app.ai.prompts.python_review import NL_TO_PYTHON, PYTHON_REVIEW, PYTHON_TUTOR
from app.ai.prompts.sql_review import NL_TO_SQL, SQL_DEBUG, SQL_OPTIMIZATION, SQL_REVIEW, SQL_TUTOR
from app.models.enums import AIFeature

REGISTRY: dict[str, PromptTemplate] = {
    t.feature: t
    for t in [
        MENTOR,
        SQL_TUTOR,
        SQL_REVIEW,
        SQL_DEBUG,
        SQL_OPTIMIZATION,
        NL_TO_SQL,
        PYTHON_TUTOR,
        PYTHON_REVIEW,
        NL_TO_PYTHON,
        ANALYSIS_REVIEW,
        INSIGHT_REVIEW,
        EDA_ASSISTANT,
        DATA_EXPLORATION,
        DOMAIN_COACH,
        CASE_COACH,
        CASE_INTERVIEWER,
        BEHAVIORAL_INTERVIEWER,
        INTERVIEW_DEBRIEF,
        COMMUNICATION_COACH,
        STORYTELLING_COACH,
        EXEC_SUMMARY,
        LEARNING_PLANNER,
        SKILL_DIAGNOSIS,
        PROJECT_REVIEW,
        KNOWLEDGE_SEARCH,
        JD_EXTRACTION,
        RESUME_REVIEW,
        CAREER_COACH,
        PORTFOLIO_REVIEW,
    ]
}

assert set(REGISTRY) == set(AIFeature), (  # noqa: S101 — a module-import-time invariant, not a runtime check
    f"Every AIFeature must have a registered PromptTemplate. Missing: {set(AIFeature) - set(REGISTRY)}"
)


def get_template(feature: str) -> PromptTemplate:
    return REGISTRY[feature]
