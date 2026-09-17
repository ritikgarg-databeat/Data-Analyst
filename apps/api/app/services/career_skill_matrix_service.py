"""Career Skill Matrix (Phase 11, spec section 22) — one row per platform
skill with real evidence counts (app/services/career_evidence.py) and a
5-level evidence-based mastery label, never calculated from a single test."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.career import CareerProfile, TargetRole
from app.models.enums import SKILL_CATEGORY_LABELS
from app.models.skill import Skill
from app.schemas.career import CareerSkillMatrixEntrySchema
from app.services.career_evidence import compute_all_skill_evidence

WEAK_MASTERY_THRESHOLD = 55.0


class CareerSkillMatrixService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _primary_role_gap_skills(self, user_id: str) -> set[str]:
        profile = self.db.execute(
            select(CareerProfile).where(CareerProfile.user_id == user_id)
        ).scalar_one_or_none()
        if profile is None or profile.primary_target_role_id is None:
            return set()
        target_role = self.db.get(TargetRole, profile.primary_target_role_id)
        if target_role is None or target_role.role_template is None:
            return set()
        return set(target_role.role_template.core_skills) | set(target_role.role_template.preferred_skills)

    def get_matrix(self, user_id: str) -> list[CareerSkillMatrixEntrySchema]:
        gap_candidates = self._primary_role_gap_skills(user_id)
        skills = self.db.execute(select(Skill).order_by(Skill.category, Skill.name)).scalars().all()
        evidence_by_slug = compute_all_skill_evidence(self.db, user_id)

        entries: list[CareerSkillMatrixEntrySchema] = []
        for skill in skills:
            evidence = evidence_by_slug[skill.slug]
            entries.append(
                CareerSkillMatrixEntrySchema(
                    skill_slug=skill.slug,
                    name=skill.name,
                    category=SKILL_CATEGORY_LABELS[skill.category],
                    mastery_score=evidence.mastery_score,
                    evidence_level=evidence.evidence_level.value,
                    exercises_passed=evidence.exercises_passed,
                    assessment_pct=None,
                    projects_count=evidence.projects_count,
                    cases_count=evidence.cases_count,
                    mock_interview_score=evidence.mock_interview_score,
                    is_gap_for_primary_role=(
                        skill.slug in gap_candidates and evidence.mastery_score < WEAK_MASTERY_THRESHOLD
                    ),
                )
            )
        return entries
