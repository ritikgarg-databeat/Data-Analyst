from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.enums import mastery_level_for_score
from app.models.skill import Skill
from app.repositories.skill import SkillRepository, UserSkillRepository
from app.schemas.skill import CreateSkillRequest, UpdateSkillRequest
from app.schemas.skill import Skill as SkillSchema
from app.schemas.skill import UserSkill as UserSkillSchema


class SkillService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SkillRepository(db)
        self.user_skill_repo = UserSkillRepository(db)

    def list_skills(self) -> list[SkillSchema]:
        return [SkillSchema.model_validate(s) for s in self.repo.list_all()]

    def get_by_slug(self, slug: str) -> SkillSchema:
        return SkillSchema.model_validate(self.get_model_by_slug(slug))

    def get_model_by_slug(self, slug: str) -> Skill:
        skill = self.repo.get_by_slug(slug)
        if skill is None:
            raise NotFoundError(f"Skill '{slug}' was not found.", details={"slug": slug})
        return skill

    def list_user_skills(self, user_id: str) -> list[UserSkillSchema]:
        skills_by_id = {s.id: s for s in self.repo.list_all()}
        user_skills = {us.skill_id: us for us in self.user_skill_repo.list_for_user(user_id)}

        results: list[UserSkillSchema] = []
        for skill_id, skill in skills_by_id.items():
            us = user_skills.get(skill_id)
            mastery_score = us.mastery_score if us else 0.0
            results.append(
                UserSkillSchema(
                    user_id=user_id,
                    skill_id=skill_id,
                    skill=SkillSchema.model_validate(skill),
                    mastery_score=mastery_score,
                    mastery_level=mastery_level_for_score(mastery_score),
                    confidence_score=us.confidence_score if us else 0.0,
                    questions_attempted=us.questions_attempted if us else 0,
                    questions_correct=us.questions_correct if us else 0,
                    last_practiced_at=us.last_practiced_at if us else None,
                    updated_at=us.updated_at if us else skill.updated_at,
                )
            )
        return sorted(results, key=lambda r: (r.skill.category, r.skill.name))

    def create(self, payload: CreateSkillRequest) -> SkillSchema:
        if self.repo.get_by_slug(payload.slug) is not None:
            raise ConflictError(f"Skill '{payload.slug}' already exists.")
        skill = Skill(
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            target_level=payload.target_level,
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return SkillSchema.model_validate(skill)

    def update(self, skill_id: str, payload: UpdateSkillRequest) -> SkillSchema:
        skill = self.repo.get_by_id(skill_id)
        if skill is None:
            raise NotFoundError(f"Skill '{skill_id}' was not found.")
        for field in ("slug", "name", "description", "category", "target_level"):
            value = getattr(payload, field)
            if value is not None:
                setattr(skill, field, value)
        self.db.commit()
        self.db.refresh(skill)
        return SkillSchema.model_validate(skill)
