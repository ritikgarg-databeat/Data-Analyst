"""Data Integrity Audit (Phase 12, spec section 78) — SQLite's foreign-key
enforcement is not enabled in this app (confirmed: no `PRAGMA foreign_keys`
anywhere in `app/core/database.py`), so an orphaned reference (e.g. an
`ExerciseAttempt` pointing at a deleted `Exercise`) would never be rejected
at write time. This is a read-only diagnostic that actually checks for it,
rather than assuming it can't happen. Primarily a developer/admin tool —
see `app/db/integrity_check_cli.py`."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentQuestion
from app.models.career import JDRequirement, ResumeEvidence, RoleTemplate, SkillGap, TargetRole
from app.models.case import Case, CaseAttempt
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import InterviewQuestion
from app.models.lesson import Lesson
from app.models.lesson_relations import LessonPrerequisite, LessonSkill
from app.models.project import Project, ProjectTemplate
from app.models.skill import Skill


@dataclass
class IntegrityCheckResult:
    name: str
    orphaned_count: int
    detail: str


@dataclass
class _Check:
    name: str
    child_model: type
    fk_column: str
    parent_model: type
    parent_column: str
    nullable: bool


_CHECKS: list[_Check] = [
    _Check("exercise_attempts.exercise_id", ExerciseAttempt, "exercise_id", Exercise, "id", False),
    _Check("exercises.lesson_id", Exercise, "lesson_id", Lesson, "id", True),
    _Check("exercises.skill_id", Exercise, "skill_id", Skill, "id", True),
    _Check("case_attempts.case_id", CaseAttempt, "case_id", Case, "id", False),
    _Check("projects.template_id", Project, "template_id", ProjectTemplate, "id", True),
    _Check("interview_questions.exercise_id", InterviewQuestion, "exercise_id", Exercise, "id", False),
    _Check("assessment_questions.exercise_id", AssessmentQuestion, "exercise_id", Exercise, "id", False),
    _Check("target_roles.role_template_id", TargetRole, "role_template_id", RoleTemplate, "id", True),
    _Check("lesson_skills.skill_id", LessonSkill, "skill_id", Skill, "id", False),
    _Check(
        "lesson_prerequisites.prerequisite_lesson_id",
        LessonPrerequisite, "prerequisite_lesson_id", Lesson, "id", False,
    ),
    _Check("jd_requirements.matched_skill_slug", JDRequirement, "matched_skill_slug", Skill, "slug", True),
    _Check("resume_evidence.skill_slug", ResumeEvidence, "skill_slug", Skill, "slug", False),
    _Check("skill_gaps.skill_slug", SkillGap, "skill_slug", Skill, "slug", False),
]


class DataIntegrityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _check_one(self, check: _Check) -> IntegrityCheckResult:
        child_col = getattr(check.child_model, check.fk_column)
        parent_col = getattr(check.parent_model, check.parent_column)
        known_values = set(self.db.execute(select(parent_col)).scalars().all())

        value_stmt = select(child_col)
        if check.nullable:
            value_stmt = value_stmt.where(child_col.is_not(None))
        rows = self.db.execute(value_stmt).scalars().all()
        orphaned = sum(1 for v in rows if v not in known_values)

        detail = (
            "OK" if orphaned == 0 else f"{orphaned} row(s) reference a missing {check.parent_model.__name__}"
        )
        return IntegrityCheckResult(name=check.name, orphaned_count=orphaned, detail=detail)

    def _duplicate_skill_slugs(self) -> IntegrityCheckResult:
        rows = self.db.execute(select(Skill.slug, func.count()).group_by(Skill.slug)).all()
        duplicates = [slug for slug, count in rows if count > 1]
        return IntegrityCheckResult(
            name="skills.slug (duplicates)",
            orphaned_count=len(duplicates),
            detail="OK" if not duplicates else f"Duplicate skill slugs: {duplicates}",
        )

    def check_all(self) -> list[IntegrityCheckResult]:
        results = [self._check_one(c) for c in _CHECKS]
        results.append(self._duplicate_skill_slugs())
        return results
