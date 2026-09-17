from sqlalchemy import select

from app.models.assessment import Assessment, AssessmentAttempt
from app.repositories.base import BaseRepository


class AssessmentRepository(BaseRepository[Assessment]):
    model = Assessment

    def get_by_module_id(self, module_id: str) -> Assessment | None:
        stmt = select(Assessment).where(Assessment.module_id == module_id, Assessment.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()


class AssessmentAttemptRepository(BaseRepository[AssessmentAttempt]):
    model = AssessmentAttempt

    def list_for_user_and_assessment(self, user_id: str, assessment_id: str) -> list[AssessmentAttempt]:
        stmt = (
            select(AssessmentAttempt)
            .where(AssessmentAttempt.user_id == user_id, AssessmentAttempt.assessment_id == assessment_id)
            .order_by(AssessmentAttempt.started_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
