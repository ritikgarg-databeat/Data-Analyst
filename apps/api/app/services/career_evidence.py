"""Shared, real-data skill-evidence aggregation for the Career layer (Phase
11) — every count here is a genuine join against ExerciseAttempt/CaseAttempt/
Project/Interview rows, never an estimate. Used by career_readiness_service,
resume_service (gap analysis), portfolio_service (gap detection), and the
Career Skill Matrix router. Reads UserSkill.mastery_score (computed by the
existing, deterministic MasteryService) as ground truth for mastery — never
recomputes it."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import Case, CaseAttempt
from app.models.enums import CareerEvidenceLevel, CaseAttemptStatus, InterviewMode, InterviewStatus
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import Interview, InterviewQuestion, InterviewQuestionAttempt
from app.models.project import Project, ProjectTemplate
from app.models.skill import Skill
from app.models.user_skill import UserSkill

MOCK_INTERVIEW_MODES = {InterviewMode.MOCK, InterviewMode.COMPANY_STYLE, InterviewMode.FINAL_READINESS}
INTERVIEW_READY_SCORE_THRESHOLD = 70.0
PRACTICED_EXERCISE_THRESHOLD = 3


@dataclass
class SkillEvidence:
    skill_slug: str
    mastery_score: float
    exercises_passed: int
    projects_count: int
    cases_count: int
    mock_interview_score: float | None

    @property
    def evidence_level(self) -> CareerEvidenceLevel:
        applied = self.projects_count > 0 or self.cases_count > 0
        interview_ready = (
            self.mock_interview_score is not None
            and self.mock_interview_score >= INTERVIEW_READY_SCORE_THRESHOLD
        )
        if applied and interview_ready:
            return CareerEvidenceLevel.DEMONSTRATED
        if interview_ready:
            return CareerEvidenceLevel.INTERVIEW_READY
        if applied:
            return CareerEvidenceLevel.APPLIED
        if self.exercises_passed >= PRACTICED_EXERCISE_THRESHOLD:
            return CareerEvidenceLevel.PRACTICED
        return CareerEvidenceLevel.LEARNED


def get_skill_by_slug(db: Session, skill_slug: str) -> Skill | None:
    return db.execute(select(Skill).where(Skill.slug == skill_slug)).scalar_one_or_none()


def mastery_score_for_skill(db: Session, user_id: str, skill_id: str) -> float:
    row = db.execute(
        select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
    ).scalar_one_or_none()
    return row.mastery_score if row else 0.0


def _exercises_passed(db: Session, user_id: str, skill_id: str) -> int:
    stmt = (
        select(ExerciseAttempt)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(Exercise.skill_id == skill_id, ExerciseAttempt.user_id == user_id)
        .where(ExerciseAttempt.score.is_not(None), ExerciseAttempt.score >= 70)
    )
    return len(db.execute(stmt).scalars().all())


def _projects_count(db: Session, user_id: str, skill_slug: str) -> int:
    stmt = (
        select(Project)
        .join(ProjectTemplate, ProjectTemplate.id == Project.template_id)
        .where(Project.user_id == user_id, Project.status == CaseAttemptStatus.COMPLETED)
    )
    return sum(
        1 for p in db.execute(stmt).scalars().all() if skill_slug in (p.template.required_skills or [])
    )


def _cases_count(db: Session, user_id: str, skill_slug: str) -> int:
    stmt = (
        select(CaseAttempt)
        .join(Case, Case.id == CaseAttempt.case_id)
        .where(CaseAttempt.user_id == user_id, CaseAttempt.status == CaseAttemptStatus.COMPLETED)
    )
    return sum(1 for a in db.execute(stmt).scalars().all() if skill_slug in (a.case.skills or []))


def _mock_interview_score(db: Session, user_id: str, skill_id: str) -> float | None:
    stmt = (
        select(ExerciseAttempt.score)
        .select_from(InterviewQuestionAttempt)
        .join(Interview, Interview.id == InterviewQuestionAttempt.interview_id)
        .join(InterviewQuestion, InterviewQuestion.id == InterviewQuestionAttempt.interview_question_id)
        .join(Exercise, Exercise.id == InterviewQuestion.exercise_id)
        .join(ExerciseAttempt, ExerciseAttempt.id == InterviewQuestionAttempt.exercise_attempt_id)
        .where(
            Interview.user_id == user_id,
            Interview.status == InterviewStatus.COMPLETED,
            Interview.mode.in_(MOCK_INTERVIEW_MODES),
            Exercise.skill_id == skill_id,
            ExerciseAttempt.score.is_not(None),
        )
    )
    scores = [s for s in db.execute(stmt).scalars().all() if s is not None]
    return round(sum(scores) / len(scores), 1) if scores else None


def compute_skill_evidence(db: Session, user_id: str, skill_slug: str) -> SkillEvidence:
    skill = get_skill_by_slug(db, skill_slug)
    if skill is None:
        return SkillEvidence(skill_slug, 0.0, 0, 0, 0, None)
    return SkillEvidence(
        skill_slug=skill_slug,
        mastery_score=mastery_score_for_skill(db, user_id, skill.id),
        exercises_passed=_exercises_passed(db, user_id, skill.id),
        projects_count=_projects_count(db, user_id, skill_slug),
        cases_count=_cases_count(db, user_id, skill_slug),
        mock_interview_score=_mock_interview_score(db, user_id, skill.id),
    )


def compute_all_skill_evidence(db: Session, user_id: str) -> dict[str, SkillEvidence]:
    """Same result as calling `compute_skill_evidence` once per skill, but
    ~O(1) queries instead of ~O(5 * skill_count) — found via a Phase 12
    performance pass: the Career Skill Matrix (38 skills) took ~725ms
    because `compute_skill_evidence`'s five queries (mastery, exercises,
    projects, cases, mock-interview) were each re-run per skill, re-fetching
    the SAME "all completed projects"/"all completed case attempts" rows 38
    times over. This fetches each real source table exactly once and
    aggregates in Python."""
    skills = db.execute(select(Skill)).scalars().all()
    skill_by_id = {s.id: s for s in skills}

    mastery_by_skill_id = {
        us.skill_id: us.mastery_score
        for us in db.execute(select(UserSkill).where(UserSkill.user_id == user_id)).scalars().all()
    }

    exercises_passed_by_skill_id: dict[str, int] = {}
    attempt_rows = db.execute(
        select(Exercise.skill_id)
        .select_from(ExerciseAttempt)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.score.is_not(None),
            ExerciseAttempt.score >= 70,
        )
    ).scalars().all()
    for skill_id in attempt_rows:
        if skill_id is not None:
            exercises_passed_by_skill_id[skill_id] = exercises_passed_by_skill_id.get(skill_id, 0) + 1

    projects_count_by_slug: dict[str, int] = {}
    completed_projects = db.execute(
        select(Project)
        .join(ProjectTemplate, ProjectTemplate.id == Project.template_id)
        .where(Project.user_id == user_id, Project.status == CaseAttemptStatus.COMPLETED)
    ).scalars().all()
    for project in completed_projects:
        for slug in project.template.required_skills or []:
            projects_count_by_slug[slug] = projects_count_by_slug.get(slug, 0) + 1

    cases_count_by_slug: dict[str, int] = {}
    completed_cases = db.execute(
        select(CaseAttempt)
        .join(Case, Case.id == CaseAttempt.case_id)
        .where(CaseAttempt.user_id == user_id, CaseAttempt.status == CaseAttemptStatus.COMPLETED)
    ).scalars().all()
    for attempt in completed_cases:
        for slug in attempt.case.skills or []:
            cases_count_by_slug[slug] = cases_count_by_slug.get(slug, 0) + 1

    mock_scores_by_skill_id: dict[str, list[float]] = {}
    mock_rows = db.execute(
        select(Exercise.skill_id, ExerciseAttempt.score)
        .select_from(InterviewQuestionAttempt)
        .join(Interview, Interview.id == InterviewQuestionAttempt.interview_id)
        .join(InterviewQuestion, InterviewQuestion.id == InterviewQuestionAttempt.interview_question_id)
        .join(Exercise, Exercise.id == InterviewQuestion.exercise_id)
        .join(ExerciseAttempt, ExerciseAttempt.id == InterviewQuestionAttempt.exercise_attempt_id)
        .where(
            Interview.user_id == user_id,
            Interview.status == InterviewStatus.COMPLETED,
            Interview.mode.in_(MOCK_INTERVIEW_MODES),
            ExerciseAttempt.score.is_not(None),
        )
    ).all()
    for skill_id, score in mock_rows:
        if skill_id is not None and score is not None:
            mock_scores_by_skill_id.setdefault(skill_id, []).append(score)

    result: dict[str, SkillEvidence] = {}
    for skill_id, skill in skill_by_id.items():
        scores = mock_scores_by_skill_id.get(skill_id)
        result[skill.slug] = SkillEvidence(
            skill_slug=skill.slug,
            mastery_score=mastery_by_skill_id.get(skill_id, 0.0),
            exercises_passed=exercises_passed_by_skill_id.get(skill_id, 0),
            projects_count=projects_count_by_slug.get(skill.slug, 0),
            cases_count=cases_count_by_slug.get(skill.slug, 0),
            mock_interview_score=round(sum(scores) / len(scores), 1) if scores else None,
        )
    return result
