"""Job-Ready Checklist (Phase 12, spec section 62) — a thin composition
over already-computed, real signals (mastery scores, completed cases/
projects/interviews, portfolio/resume/JD state). Every item is a genuine
boolean derived from real rows; nothing here is a fabricated milestone.
Grouped exactly as the spec's own example groups them (Technical/Analytics/
Data Stack/Applied/Interview/Career)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.career import JDAnalysis, JobDescription, Portfolio, PortfolioItem, Resume
from app.models.case import CaseAttempt
from app.models.enums import CaseAttemptStatus, InterviewMode, InterviewStatus, PrivacyLevel, SkillCategory
from app.models.interview import Interview
from app.models.project import Project
from app.models.skill import Skill
from app.models.user_skill import UserSkill

READY_MASTERY_THRESHOLD = 60.0  # "Competent" per the platform's mastery-level scale
MOCK_INTERVIEW_MODES = {InterviewMode.MOCK, InterviewMode.COMPANY_STYLE, InterviewMode.FINAL_READINESS}


class JobReadyChecklistService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _category_ready(self, user_id: str, category: SkillCategory) -> bool:
        skills = self.db.execute(select(Skill.id).where(Skill.category == category)).scalars().all()
        if not skills:
            return False
        scores = self.db.execute(
            select(UserSkill.mastery_score).where(
                UserSkill.user_id == user_id, UserSkill.skill_id.in_(skills)
            )
        ).scalars().all()
        if not scores:
            return False
        return (sum(scores) / len(skills)) >= READY_MASTERY_THRESHOLD

    def _skill_ready(self, user_id: str, slug: str) -> bool:
        skill = self.db.execute(select(Skill.id).where(Skill.slug == slug)).scalar_one_or_none()
        if skill is None:
            return False
        score = self.db.execute(
            select(UserSkill.mastery_score).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill)
        ).scalar_one_or_none()
        return bool(score) and score >= READY_MASTERY_THRESHOLD

    def _has_completed_case(self, user_id: str) -> bool:
        return self.db.execute(
            select(CaseAttempt.id).where(
                CaseAttempt.user_id == user_id, CaseAttempt.status == CaseAttemptStatus.COMPLETED
            ).limit(1)
        ).first() is not None

    def _has_completed_project(self, user_id: str) -> bool:
        return self.db.execute(
            select(Project.id).where(
                Project.user_id == user_id, Project.status == CaseAttemptStatus.COMPLETED
            ).limit(1)
        ).first() is not None

    def _has_portfolio_ready_item(self, user_id: str) -> bool:
        portfolio_id = self.db.execute(
            select(Portfolio.id).where(Portfolio.user_id == user_id)
        ).scalar_one_or_none()
        if portfolio_id is None:
            return False
        return self.db.execute(
            select(PortfolioItem.id).where(
                PortfolioItem.portfolio_id == portfolio_id, PortfolioItem.privacy != PrivacyLevel.PRIVATE
            ).limit(1)
        ).first() is not None

    def _has_mock_interview(self, user_id: str) -> bool:
        return self.db.execute(
            select(Interview.id).where(
                Interview.user_id == user_id,
                Interview.status == InterviewStatus.COMPLETED,
                Interview.mode.in_(MOCK_INTERVIEW_MODES),
            ).limit(1)
        ).first() is not None

    def _has_resume(self, user_id: str) -> bool:
        stmt = select(Resume.id).where(Resume.user_id == user_id).limit(1)
        return self.db.execute(stmt).first() is not None

    def _has_jd_analysis(self, user_id: str) -> bool:
        return self.db.execute(
            select(JDAnalysis.id)
            .join(JobDescription, JobDescription.id == JDAnalysis.job_description_id)
            .where(JobDescription.user_id == user_id)
            .limit(1)
        ).first() is not None

    def get_checklist(self, user_id: str) -> list[dict]:
        return [
            {
                "group": "Technical",
                "items": [
                    {"label": "SQL", "ready": self._category_ready(user_id, SkillCategory.SQL)},
                    {"label": "Python", "ready": self._category_ready(user_id, SkillCategory.PYTHON)},
                    {"label": "Excel", "ready": self._category_ready(user_id, SkillCategory.EXCEL)},
                ],
            },
            {
                "group": "Analytics",
                "items": [
                    {"label": "Statistics", "ready": self._category_ready(user_id, SkillCategory.STATISTICS)},
                    {
                        "label": "Product Analytics",
                        "ready": self._category_ready(user_id, SkillCategory.PRODUCT_ANALYTICS),
                    },
                    {
                        "label": "Business Analytics",
                        "ready": self._category_ready(user_id, SkillCategory.BUSINESS_ANALYTICS),
                    },
                ],
            },
            {
                "group": "Data Stack",
                "items": [
                    {
                        "label": "Warehousing",
                        "ready": self._category_ready(user_id, SkillCategory.DATA_WAREHOUSING),
                    },
                    {
                        "label": "Modeling",
                        "ready": self._category_ready(user_id, SkillCategory.DATA_MODELING),
                    },
                    {"label": "dbt", "ready": self._skill_ready(user_id, "dbt")},
                    {
                        "label": "Data Quality",
                        "ready": self._skill_ready(user_id, "data-quality-engineering"),
                    },
                ],
            },
            {
                "group": "Applied",
                "items": [
                    {"label": "Cases", "ready": self._has_completed_case(user_id)},
                    {"label": "Projects", "ready": self._has_completed_project(user_id)},
                    {"label": "Portfolio", "ready": self._has_portfolio_ready_item(user_id)},
                ],
            },
            {
                "group": "Interview",
                "items": [
                    {"label": "SQL", "ready": self._skill_ready(user_id, "interview-sql")},
                    {"label": "Case", "ready": self._skill_ready(user_id, "analytics-case-studies")},
                    {"label": "Behavioral", "ready": self._skill_ready(user_id, "behavioral-interviewing")},
                    {"label": "Mock Interview", "ready": self._has_mock_interview(user_id)},
                ],
            },
            {
                "group": "Career",
                "items": [
                    {"label": "Resume", "ready": self._has_resume(user_id)},
                    {"label": "JD Preparation", "ready": self._has_jd_analysis(user_id)},
                    {"label": "Skill Gaps", "ready": self._has_jd_analysis(user_id)},
                ],
            },
        ]
