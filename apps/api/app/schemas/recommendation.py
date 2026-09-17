from typing import Literal

from pydantic import BaseModel

from app.schemas.lesson import Lesson

RecommendationReason = Literal[
    "incomplete_prerequisite", "next_in_module", "weak_skill", "unfinished_lesson", "review"
]


class RecommendationItem(BaseModel):
    lesson: Lesson
    reason: RecommendationReason
    explanation: str
