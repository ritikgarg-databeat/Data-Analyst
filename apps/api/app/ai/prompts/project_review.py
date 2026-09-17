"""AI Project Review (spec section 59) — end-of-Phase-8-project review across
framing/data model/SQL/Python/statistics/visualizations/findings/
recommendations/communication. Reads the real, already-submitted Project
artifacts; does not re-grade anything the platform already scores."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AIProjectReviewResult

PROJECT_REVIEW = PromptTemplate(
    feature=AIFeature.PROJECT_REVIEW,
    version="1.0",
    purpose="End-of-project review (spec section 59): strong/needs-improvement/technical/business/"
    "communication + top 3 improvements.",
    input_schema={
        "project": "real ProjectTemplate + milestones",
        "artifacts": "real ProjectArtifact list "
        "(business framing, data model, SQL/Python work, findings, recommendations, communication)",
    },
    output_schema=AIProjectReviewResult,
    default_mode=AIMode.REVIEWER,
    instructions="""Review this completed project end-to-end using the real artifacts given below \
(whichever of business framing / data model / SQL / Python / statistics / visualizations / findings \
/ recommendations / communication were actually submitted — don't invent commentary on a section \
that wasn't provided). Separate `strong` and `needs_improvement` at a high level, then break out \
`technical`, `business`, and `communication` specific notes, and close with exactly the top 3 most \
impactful improvements the learner should make.""",
)
