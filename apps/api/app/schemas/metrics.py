from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMSchema


class InterviewQA(BaseModel):
    question: str
    answer: str


class MetricDefinitionSchema(ORMSchema):
    id: str
    slug: str
    name: str
    category: str
    definition: str
    formula: str | None = None
    examples: list[str] = []
    sql_example: str | None = None
    python_example: str | None = None
    common_mistakes: list[str] = []
    related_metrics: list[str] = []
    business_questions: list[str] = []
    interview_questions: list[InterviewQA] = []
    display_order: int
    created_at: datetime
    updated_at: datetime
