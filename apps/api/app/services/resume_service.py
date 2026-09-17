"""Resume Analyzer (Phase 11, spec sections 10-13). Resume Quality Review
SCORES (quality/clarity/impact) are computed deterministically here from the
resume's own real text — never by AI (see ResumeReview's model docstring and
app/ai/AUTHORITY.md) — AI (RESUME_REVIEW) only supplies the qualitative
summary/issues/suggestions layered on top. Evidence extraction is plain
keyword matching against the real skill taxonomy, never a fabricated
metric/employer/achievement."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.career import Resume, ResumeEvidence, ResumeReview, ResumeVersion, TargetRole
from app.models.skill import Skill
from app.schemas.resume import (
    CreateResumeRequest,
    CreateResumeVersionRequest,
    ResumeGapAnalysisResponse,
    ResumeGapEntrySchema,
    ResumeReviewSchema,
    ResumeSchema,
    ResumeVersionSchema,
    UpdateResumeRequest,
)
from app.services.ai_career_service import AICareerService

_ACTION_VERBS = {
    "led", "built", "designed", "analyzed", "developed", "created", "managed", "improved", "reduced",
    "increased", "automated", "implemented", "optimized", "launched", "delivered", "drove", "owned",
}
_MAX_CLEAR_LINE_LENGTH = 160


def _lines(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def _clarity_score(lines: list[str]) -> float:
    if not lines:
        return 0.0
    reasonable = sum(1 for line in lines if len(line) <= _MAX_CLEAR_LINE_LENGTH)
    return round(100 * reasonable / len(lines), 1)


def _impact_score(lines: list[str]) -> float:
    if not lines:
        return 0.0
    with_evidence = sum(
        1 for line in lines
        if re.search(r"\d", line) or line.split()[0].lower().strip(".,:-") in _ACTION_VERBS
    )
    return round(100 * with_evidence / len(lines), 1)


class ResumeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Resume + version CRUD ---------------------------------------------------

    def list_resumes(self, user_id: str) -> list[ResumeSchema]:
        rows = self.db.execute(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        ).scalars().all()
        return [ResumeSchema.model_validate(r) for r in rows]

    def create_resume(self, user_id: str, payload: CreateResumeRequest) -> ResumeSchema:
        resume = Resume(user_id=user_id, title=payload.title, is_primary=payload.is_primary)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return ResumeSchema.model_validate(resume)

    def _get_owned_resume(self, user_id: str, resume_id: str) -> Resume:
        resume = self.db.get(Resume, resume_id)
        if resume is None or resume.user_id != user_id:
            raise NotFoundError("Resume was not found.")
        return resume

    def update_resume(self, user_id: str, resume_id: str, payload: UpdateResumeRequest) -> ResumeSchema:
        resume = self._get_owned_resume(user_id, resume_id)
        if payload.title is not None:
            resume.title = payload.title
        if payload.is_primary is not None:
            resume.is_primary = payload.is_primary
        self.db.commit()
        self.db.refresh(resume)
        return ResumeSchema.model_validate(resume)

    def delete_resume(self, user_id: str, resume_id: str) -> None:
        resume = self._get_owned_resume(user_id, resume_id)
        self.db.delete(resume)
        self.db.commit()

    def create_version(
        self, user_id: str, resume_id: str, payload: CreateResumeVersionRequest
    ) -> ResumeVersionSchema:
        resume = self._get_owned_resume(user_id, resume_id)
        self.db.query(ResumeVersion).filter(ResumeVersion.resume_id == resume_id).update(
            {"is_current": False}
        )
        next_number = (
            self.db.execute(
                select(ResumeVersion.version_number)
                .where(ResumeVersion.resume_id == resume_id)
                .order_by(ResumeVersion.version_number.desc())
            ).scalars().first()
            or 0
        ) + 1
        version = ResumeVersion(
            resume_id=resume.id,
            version_number=next_number,
            source=payload.source,
            raw_text=payload.raw_text,
            file_name=payload.file_name,
            is_current=True,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return ResumeVersionSchema.model_validate(version)

    def _get_owned_version(self, user_id: str, version_id: str) -> ResumeVersion:
        version = self.db.get(ResumeVersion, version_id)
        if version is None or version.resume.user_id != user_id:
            raise NotFoundError("Resume version was not found.")
        return version

    def get_version(self, user_id: str, version_id: str) -> ResumeVersionSchema:
        return ResumeVersionSchema.model_validate(self._get_owned_version(user_id, version_id))

    # --- Evidence extraction (deterministic) ------------------------------------------

    def extract_evidence(self, user_id: str, version_id: str) -> list[ResumeEvidence]:
        version = self._get_owned_version(user_id, version_id)
        skills = self.db.execute(select(Skill)).scalars().all()
        lines = _lines(version.raw_text)
        lowered_lines = [(line, line.lower()) for line in lines]

        self.db.query(ResumeEvidence).filter(ResumeEvidence.resume_version_id == version_id).delete()
        evidence: list[ResumeEvidence] = []
        for skill in skills:
            needle = skill.name.lower()
            slug_needle = skill.slug.replace("-", " ")
            match_line = next(
                (
                    original
                    for original, lowered in lowered_lines
                    if re.search(rf"\b{re.escape(needle)}\b", lowered)
                    or re.search(rf"\b{re.escape(slug_needle)}\b", lowered)
                ),
                None,
            )
            if match_line:
                evidence.append(
                    ResumeEvidence(
                        resume_version_id=version_id, skill_slug=skill.slug, evidence_text=match_line,
                        confidence=1.0,
                    )
                )
        self.db.add_all(evidence)
        self.db.commit()
        return evidence

    # --- Quality review -----------------------------------------------------------------

    def review(
        self, user_id: str, version_id: str, target_role_title: str | None = None
    ) -> ResumeReviewSchema:
        version = self._get_owned_version(user_id, version_id)
        lines = _lines(version.raw_text)
        clarity = _clarity_score(lines)
        impact = _impact_score(lines)
        quality = round((clarity + impact) / 2, 1)

        evidence_rows = self.db.execute(
            select(ResumeEvidence).where(ResumeEvidence.resume_version_id == version_id)
        ).scalars().all()
        ai_response = AICareerService(self.db).review_resume(
            user_id,
            resume_text=version.raw_text,
            target_role=target_role_title,
            evidence=[{"skill_slug": e.skill_slug, "evidence_text": e.evidence_text} for e in evidence_rows],
        )
        issues: list[str] = []
        suggestions: list[str] = []
        if ai_response.structured_valid and ai_response.structured:
            issues = ai_response.structured.get("issues", [])
            suggestions = ai_response.structured.get("suggestions", [])

        review = ResumeReview(
            resume_version_id=version_id, quality_score=quality, clarity_score=clarity, impact_score=impact,
            issues=issues, suggestions=suggestions, ai_generated=True,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return ResumeReviewSchema.model_validate(review)

    # --- Gap analysis --------------------------------------------------------------------

    def gap_analysis(
        self, user_id: str, version_id: str, target_role_id: str | None
    ) -> ResumeGapAnalysisResponse:
        self._get_owned_version(user_id, version_id)
        evidenced_slugs = {
            e.skill_slug
            for e in self.db.execute(
                select(ResumeEvidence).where(ResumeEvidence.resume_version_id == version_id)
            ).scalars().all()
        }

        target_skills: set[str] = set()
        if target_role_id:
            target_role = self.db.get(TargetRole, target_role_id)
            if (
                target_role is not None
                and target_role.user_id == user_id
                and target_role.role_template is not None
            ):
                target_skills = set(target_role.role_template.core_skills) | set(
                    target_role.role_template.preferred_skills
                )

        gaps = [
            ResumeGapEntrySchema(skill_slug=slug, has_evidence=slug in evidenced_slugs)
            for slug in sorted(target_skills)
        ]
        return ResumeGapAnalysisResponse(
            resume_version_id=version_id, target_role_id=target_role_id, gaps=gaps
        )
