from sqlalchemy import select

from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.repositories.base import BaseRepository


class SkillRepository(BaseRepository[Skill]):
    model = Skill

    def list_all(self, *, active_only: bool = True) -> list[Skill]:  # noqa: ARG002
        stmt = select(Skill).order_by(Skill.category, Skill.name)
        return list(self.db.execute(stmt).scalars().all())


class UserSkillRepository(BaseRepository[UserSkill]):
    model = UserSkill

    def list_for_user(self, user_id: str) -> list[UserSkill]:
        stmt = select(UserSkill).where(UserSkill.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def get(self, user_id: str, skill_id: str) -> UserSkill | None:
        stmt = select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
        return self.db.execute(stmt).scalar_one_or_none()
