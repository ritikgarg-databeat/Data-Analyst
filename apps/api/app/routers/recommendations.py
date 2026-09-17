from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_lesson_service, get_recommendation_service
from app.schemas.recommendation import RecommendationItem
from app.services.lesson_service import LessonService
from app.services.recommendations import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationItem])
def get_recommendations(
    user_id: CurrentUserId,
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
    lesson_service: Annotated[LessonService, Depends(get_lesson_service)],
    limit: int = Query(default=5, ge=1, le=20),
) -> list[RecommendationItem]:
    recs = service.get_next(user_id, limit=limit)
    return [
        RecommendationItem(
            lesson=lesson_service.to_schema(r.lesson), reason=r.reason, explanation=r.explanation
        )
        for r in recs
    ]
