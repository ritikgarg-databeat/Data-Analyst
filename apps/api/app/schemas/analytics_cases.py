from app.schemas.exercise import Exercise as ExerciseSchema
from app.schemas.exercise import RubricCriterionSchema


class AnalyticsCaseSchema(ExerciseSchema):
    """A Business/Product analytics case (spec sections 33 & 44) — an
    Exercise (`BUSINESS_REASONING`/`DATA_INTERPRETATION`) tagged
    `case-study`, with its richer case-framing fields surfaced from the
    content file. Reuses the whole Exercise/ExerciseAttempt pipeline for
    submission and progress tracking rather than a parallel model."""

    prompt: str
    business_context: str | None = None
    stakeholder: str | None = None
    constraints: list[str] = []
    expected_deliverables: list[str] = []
    rubric: list[RubricCriterionSchema] = []
