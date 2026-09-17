"""Job Description Analyzer + Skill Gap + Preparation Plan + Job Preparation
Workspace (Phase 11, spec sections 5-16). Extraction runs deterministic
keyword matching against the real skill taxonomy FIRST (so this works with
AI disabled), then optionally enriches with the AI JD_EXTRACTION feature —
every `matched_skill_slug` (deterministic or AI-suggested) is re-validated
against real Skill rows before being persisted, so a requirement can never
silently reference a skill that doesn't exist (spec section 7)."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.career import (
    JDAnalysis,
    JDRequirement,
    JobDescription,
    JobPreparationWorkspace,
    SkillGap,
    TargetRole,
)
from app.models.case import Case
from app.models.enums import (
    InterviewQuestionType,
    JDRequirementKind,
    JDRequirementPriority,
    SkillCategory,
)
from app.models.exercise import Exercise
from app.models.interview import InterviewQuestion
from app.models.project import ProjectTemplate
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.schemas.jobs import (
    AnalyzeJobDescriptionRequest,
    CreateJobDescriptionRequest,
    CreateJobPrepWorkspaceRequest,
    JDAnalysisSchema,
    JDComparisonEntrySchema,
    JDComparisonResponse,
    JDInterviewPlanResponse,
    JobDescriptionSchema,
    JobPreparationWorkspaceSchema,
    PreparationPlanResponse,
    PreparationTaskSchema,
    SkillGapSchema,
    SkillGapTableResponse,
    UpdateJobDescriptionRequest,
    UpdateJobPrepWorkspaceRequest,
)
from app.services.ai_career_service import AICareerService
from app.services.career_evidence import get_skill_by_slug, mastery_score_for_skill

DEFAULT_PRIORITY_WEIGHTS: dict[str, float] = {
    JDRequirementPriority.MUST_HAVE: 3.0,
    JDRequirementPriority.STRONGLY_PREFERRED: 2.0,
    JDRequirementPriority.NICE_TO_HAVE: 1.0,
}
MASTERY_TARGET_FOR_FULL_COVERAGE = 70.0
CATEGORY_TO_INTERVIEW_TYPE: dict[str, str] = {
    cat.value: cat.value for cat in SkillCategory if cat.value in InterviewQuestionType.__members__
}


class JDService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Job description CRUD ---------------------------------------------------

    def list_job_descriptions(self, user_id: str) -> list[JobDescriptionSchema]:
        rows = self.db.execute(
            select(JobDescription)
            .where(JobDescription.user_id == user_id)
            .order_by(JobDescription.created_at.desc())
        ).scalars().all()
        return [JobDescriptionSchema.model_validate(r) for r in rows]

    def _get_owned(self, user_id: str, jd_id: str) -> JobDescription:
        jd = self.db.get(JobDescription, jd_id)
        if jd is None or jd.user_id != user_id:
            raise NotFoundError("Job description was not found.")
        return jd

    def get_job_description(self, user_id: str, jd_id: str) -> JobDescriptionSchema:
        return JobDescriptionSchema.model_validate(self._get_owned(user_id, jd_id))

    def create_job_description(
        self, user_id: str, payload: CreateJobDescriptionRequest
    ) -> JobDescriptionSchema:
        if payload.target_role_id:
            role = self.db.get(TargetRole, payload.target_role_id)
            if role is None or role.user_id != user_id:
                raise NotFoundError("Target role was not found.")
        jd = JobDescription(
            user_id=user_id,
            target_role_id=payload.target_role_id,
            company=payload.company,
            title=payload.title,
            source=payload.source,
            raw_text=payload.raw_text,
            location=payload.location,
            notes=payload.notes,
        )
        self.db.add(jd)
        self.db.commit()
        self.db.refresh(jd)
        return JobDescriptionSchema.model_validate(jd)

    def update_job_description(
        self, user_id: str, jd_id: str, payload: UpdateJobDescriptionRequest
    ) -> JobDescriptionSchema:
        jd = self._get_owned(user_id, jd_id)
        for field in ("company", "title", "notes", "target_role_id"):
            value = getattr(payload, field)
            if value is not None:
                setattr(jd, field, value)
        self.db.commit()
        self.db.refresh(jd)
        return JobDescriptionSchema.model_validate(jd)

    def delete_job_description(self, user_id: str, jd_id: str) -> None:
        jd = self._get_owned(user_id, jd_id)
        self.db.delete(jd)
        self.db.commit()

    # --- Extraction ---------------------------------------------------------------

    def _deterministic_matches(self, raw_text: str, skills: list[Skill]) -> list[dict]:
        lowered = raw_text.lower()
        matches = []
        for skill in skills:
            needle = skill.name.lower()
            if re.search(rf"\b{re.escape(needle)}\b", lowered) or re.search(
                rf"\b{re.escape(skill.slug.replace('-', ' '))}\b", lowered
            ):
                matches.append(
                    {
                        "raw_text": skill.name,
                        "kind": JDRequirementKind.SKILL,
                        "priority": JDRequirementPriority.MUST_HAVE,
                        "matched_skill_slug": skill.slug,
                        "confidence": 1.0,
                    }
                )
        return matches

    def extract_requirements(self, user_id: str, jd_id: str) -> list[JDRequirement]:
        jd = self._get_owned(user_id, jd_id)
        known_skills = self.db.execute(select(Skill)).scalars().all()
        known_slugs = {s.slug for s in known_skills}

        drafts = self._deterministic_matches(jd.raw_text, known_skills)

        ai_response = AICareerService(self.db).extract_jd_requirements(
            user_id, raw_text=jd.raw_text, known_skill_slugs=sorted(known_slugs)
        )
        if ai_response.structured_valid and ai_response.structured:
            ai_requirements = ai_response.structured.get("requirements", [])
            seen_texts = {d["raw_text"].lower() for d in drafts}
            for req in ai_requirements:
                if req.get("raw_text", "").lower() in seen_texts:
                    continue
                matched_slug = req.get("matched_skill_slug")
                if matched_slug not in known_slugs:
                    matched_slug = None  # never trust an unvalidated slug (spec section 7)
                try:
                    kind = JDRequirementKind(req.get("kind"))
                except ValueError:
                    kind = JDRequirementKind.RESPONSIBILITY
                try:
                    priority = JDRequirementPriority(req.get("priority"))
                except ValueError:
                    priority = JDRequirementPriority.NICE_TO_HAVE
                drafts.append(
                    {
                        "raw_text": req.get("raw_text", "")[:2000],
                        "kind": kind,
                        "priority": priority,
                        "matched_skill_slug": matched_slug,
                        "confidence": None,
                    }
                )

        self.db.query(JDRequirement).filter(JDRequirement.job_description_id == jd_id).delete()
        requirements = [JDRequirement(job_description_id=jd_id, **draft) for draft in drafts]
        self.db.add_all(requirements)
        self.db.commit()
        return requirements

    # --- Skill gaps -----------------------------------------------------------------

    def compute_skill_gaps(self, user_id: str, jd_id: str) -> SkillGapTableResponse:
        self._get_owned(user_id, jd_id)
        requirements = self.db.execute(
            select(JDRequirement).where(
                JDRequirement.job_description_id == jd_id, JDRequirement.matched_skill_slug.is_not(None)
            )
        ).scalars().all()

        self.db.query(SkillGap).filter(SkillGap.job_description_id == jd_id).delete()

        # Batch-fetch every candidate Skill and this user's full UserSkill set
        # up front (matching compute_all_skill_evidence's pattern) instead of
        # re-querying both per requirement — this loop previously issued 2
        # queries per matched requirement.
        wanted_slugs = {req.matched_skill_slug for req in requirements}
        skill_by_slug = (
            {
                s.slug: s
                for s in self.db.execute(select(Skill).where(Skill.slug.in_(wanted_slugs))).scalars().all()
            }
            if wanted_slugs
            else {}
        )
        mastery_by_skill_id = {
            us.skill_id: us.mastery_score
            for us in self.db.execute(select(UserSkill).where(UserSkill.user_id == user_id)).scalars().all()
        }

        seen_slugs: set[str] = set()
        gaps: list[SkillGap] = []
        for req in requirements:
            if req.matched_skill_slug in seen_slugs:
                continue
            seen_slugs.add(req.matched_skill_slug)
            skill = skill_by_slug.get(req.matched_skill_slug)
            if skill is None:
                continue
            mastery = mastery_by_skill_id.get(skill.id, 0.0)
            gap_size = max(0.0, MASTERY_TARGET_FOR_FULL_COVERAGE - mastery)
            gaps.append(
                SkillGap(
                    user_id=user_id,
                    job_description_id=jd_id,
                    skill_slug=req.matched_skill_slug,
                    required=req.priority in (
                        JDRequirementPriority.MUST_HAVE, JDRequirementPriority.STRONGLY_PREFERRED
                    ),
                    priority=req.priority,
                    current_mastery_score=mastery,
                    gap_size=gap_size,
                )
            )
        self.db.add_all(gaps)
        self.db.commit()
        return SkillGapTableResponse(
            gaps=[SkillGapSchema.model_validate(g) for g in gaps],
            covered_skill_slugs=[g.skill_slug for g in gaps if g.gap_size <= 0],
        )

    # --- Readiness analysis ------------------------------------------------------------

    def analyze(self, user_id: str, jd_id: str, payload: AnalyzeJobDescriptionRequest) -> JDAnalysisSchema:
        self._get_owned(user_id, jd_id)
        gap_table = self.compute_skill_gaps(user_id, jd_id)
        weights = {**DEFAULT_PRIORITY_WEIGHTS, **(payload.weights or {})}

        total_weight = 0.0
        weighted_coverage = 0.0
        for gap in gap_table.gaps:
            weight = weights.get(gap.priority, 1.0) if gap.priority else 1.0
            coverage = min(1.0, gap.current_mastery_score / MASTERY_TARGET_FOR_FULL_COVERAGE)
            total_weight += weight
            weighted_coverage += weight * coverage

        readiness_score = round(100 * weighted_coverage / total_weight, 1) if total_weight else 0.0
        summary = (
            f"{len(gap_table.gaps)} skill(s) matched from this job description. "
            f"Estimated readiness (platform estimate only, not a hiring guarantee): {readiness_score}%."
            if gap_table.gaps
            else "No requirements could be matched to a known platform skill yet — try Extract Requirements "
            "first."
        )

        analysis = JDAnalysis(
            job_description_id=jd_id,
            readiness_score=readiness_score,
            weights={k.value if hasattr(k, "value") else k: v for k, v in weights.items()},
            breakdown={"gap_count": len(gap_table.gaps), "covered_count": len(gap_table.covered_skill_slugs)},
            summary=summary,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return JDAnalysisSchema.model_validate(analysis)

    def get_latest_analysis(self, user_id: str, jd_id: str) -> JDAnalysisSchema | None:
        self._get_owned(user_id, jd_id)
        row = self.db.execute(
            select(JDAnalysis)
            .where(JDAnalysis.job_description_id == jd_id)
            .order_by(JDAnalysis.computed_at.desc())
        ).scalars().first()
        return JDAnalysisSchema.model_validate(row) if row else None

    # --- Preparation plan ---------------------------------------------------------------

    def generate_preparation_plan(self, user_id: str, jd_id: str) -> PreparationPlanResponse:
        gap_table = self.compute_skill_gaps(user_id, jd_id)
        # Hoisted out of the per-gap loop below — these are full-table scans
        # of Case/ProjectTemplate that don't depend on the gap being
        # processed, so re-running them once per gap was a pure N+1 scan.
        cases = self.db.execute(select(Case)).scalars().all()
        templates = self.db.execute(select(ProjectTemplate)).scalars().all()
        tasks: list[PreparationTaskSchema] = []
        for gap in gap_table.gaps:
            if gap.gap_size <= 0:
                continue
            skill = get_skill_by_slug(self.db, gap.skill_slug)
            if skill is None:
                continue
            exercises = self.db.execute(
                select(Exercise.slug)
                .where(Exercise.skill_id == skill.id, Exercise.is_active.is_(True))
                .order_by(Exercise.difficulty)
                .limit(3)
            ).scalars().all()
            case_slugs = [c.slug for c in cases if gap.skill_slug in (c.skills or [])][:2]
            project_slugs = [t.slug for t in templates if gap.skill_slug in (t.required_skills or [])][:2]
            tasks.append(
                PreparationTaskSchema(
                    skill_slug=gap.skill_slug,
                    priority=gap.priority,
                    recommended_exercise_slugs=list(exercises),
                    recommended_case_slugs=case_slugs,
                    recommended_project_slugs=project_slugs,
                )
            )
        return PreparationPlanResponse(job_description_id=jd_id, tasks=tasks)

    # --- JD-specific interview plan ---------------------------------------------------------

    def generate_interview_plan(self, user_id: str, jd_id: str) -> JDInterviewPlanResponse:
        gap_table = self.compute_skill_gaps(user_id, jd_id)
        focus_types: list[str] = []
        suggested_questions: list[str] = []
        for gap in sorted(gap_table.gaps, key=lambda g: g.gap_size, reverse=True):
            if gap.gap_size <= 0:
                continue
            skill = get_skill_by_slug(self.db, gap.skill_slug)
            if skill is None:
                continue
            interview_type = CATEGORY_TO_INTERVIEW_TYPE.get(skill.category)
            if interview_type and interview_type not in focus_types:
                focus_types.append(interview_type)

        for interview_type in focus_types[:5]:
            questions = self.db.execute(
                select(InterviewQuestion.slug)
                .where(
                    InterviewQuestion.interview_type == interview_type, InterviewQuestion.is_active.is_(True)
                )
                .limit(2)
            ).scalars().all()
            suggested_questions.extend(questions)

        return JDInterviewPlanResponse(
            job_description_id=jd_id,
            focus_interview_types=focus_types,
            suggested_question_slugs=suggested_questions,
            note=(
                "This is an estimated prep aid based on this job description's own requirement mix — "
                "it is not a claim about this employer's actual interview process."
            ),
        )

    # --- Job Preparation Workspace -----------------------------------------------------------

    def create_workspace(
        self, user_id: str, payload: CreateJobPrepWorkspaceRequest
    ) -> JobPreparationWorkspaceSchema:
        self._get_owned(user_id, payload.job_description_id)
        existing = self.db.execute(
            select(JobPreparationWorkspace).where(
                JobPreparationWorkspace.job_description_id == payload.job_description_id
            )
        ).scalar_one_or_none()
        if existing:
            return JobPreparationWorkspaceSchema.model_validate(existing)
        workspace = JobPreparationWorkspace(user_id=user_id, job_description_id=payload.job_description_id)
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return JobPreparationWorkspaceSchema.model_validate(workspace)

    def list_workspaces(self, user_id: str) -> list[JobPreparationWorkspaceSchema]:
        rows = self.db.execute(
            select(JobPreparationWorkspace).where(JobPreparationWorkspace.user_id == user_id)
        ).scalars().all()
        return [JobPreparationWorkspaceSchema.model_validate(r) for r in rows]

    def _get_owned_workspace(self, user_id: str, workspace_id: str) -> JobPreparationWorkspace:
        workspace = self.db.get(JobPreparationWorkspace, workspace_id)
        if workspace is None or workspace.user_id != user_id:
            raise NotFoundError("Job preparation workspace was not found.")
        return workspace

    def update_workspace(
        self, user_id: str, workspace_id: str, payload: UpdateJobPrepWorkspaceRequest
    ) -> JobPreparationWorkspaceSchema:
        workspace = self._get_owned_workspace(user_id, workspace_id)
        if payload.notes is not None:
            workspace.notes = payload.notes
        if payload.checklist is not None:
            workspace.checklist = [item.model_dump() for item in payload.checklist]
        if payload.status is not None:
            workspace.status = payload.status
        self.db.commit()
        self.db.refresh(workspace)
        return JobPreparationWorkspaceSchema.model_validate(workspace)

    # --- JD comparison ------------------------------------------------------------------------

    def compare(self, user_id: str, jd_ids: list[str] | None = None) -> JDComparisonResponse:
        """Compares specific saved JDs when `jd_ids` is given (the normal
        case — a user picks 2-5 target roles to compare), or every saved JD
        otherwise. Comparing "all" trends toward an empty
        `common_must_have_skill_slugs` as more, more-varied roles
        accumulate — that's a correct reflection of genuinely different
        roles, not a bug."""
        stmt = select(JobDescription).where(JobDescription.user_id == user_id)
        if jd_ids:
            stmt = stmt.where(JobDescription.id.in_(jd_ids))
        jds = self.db.execute(stmt).scalars().all()
        entries: list[JDComparisonEntrySchema] = []
        must_have_sets: list[set[str]] = []
        for jd in jds:
            analysis = self.db.execute(
                select(JDAnalysis)
                .where(JDAnalysis.job_description_id == jd.id)
                .order_by(JDAnalysis.computed_at.desc())
            ).scalars().first()
            requirements = self.db.execute(
                select(JDRequirement).where(
                    JDRequirement.job_description_id == jd.id,
                    JDRequirement.priority == JDRequirementPriority.MUST_HAVE,
                    JDRequirement.matched_skill_slug.is_not(None),
                )
            ).scalars().all()
            must_have_slugs = {r.matched_skill_slug for r in requirements}
            must_have_sets.append(must_have_slugs)
            gaps = self.db.execute(
                select(SkillGap).where(
                    SkillGap.job_description_id == jd.id,
                    SkillGap.priority == JDRequirementPriority.MUST_HAVE,
                    SkillGap.gap_size > 0,
                )
            ).scalars().all()
            entries.append(
                JDComparisonEntrySchema(
                    job_description_id=jd.id,
                    title=jd.title,
                    company=jd.company,
                    readiness_score=analysis.readiness_score if analysis else None,
                    must_have_gap_count=len(gaps),
                )
            )
        common = set.intersection(*must_have_sets) if must_have_sets else set()
        return JDComparisonResponse(entries=entries, common_must_have_skill_slugs=sorted(common))
