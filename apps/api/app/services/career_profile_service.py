"""Career Profile, Target Roles, Role Templates, the Career Dashboard, and
the auto-generated Career Progress Timeline (Phase 11). Milestones are never
freeform-authored — `sync_milestones` scans real completed events elsewhere
in the platform and upserts idempotently (skipping anything already
recorded), the same "sync on read" shape as AchievementService, so this
phase never needs to hook into Phase 1-10 services' own commit paths."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models.career import (
    Achievement,
    CareerAssessment,
    CareerGoal,
    CareerMilestone,
    CareerProfile,
    JobDescription,
    RoleTemplate,
    TargetRole,
    UserAchievement,
)
from app.models.case import CaseAttempt
from app.models.enums import (
    CareerGoalStatus,
    CareerMilestoneType,
    CareerReadinessLevel,
    CaseAttemptStatus,
    InterviewStatus,
    MasteryLevel,
)
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import Interview
from app.models.project import Project
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.schemas.career import (
    CareerDashboardSchema,
    CareerGoalSchema,
    CareerMilestoneSchema,
    CareerProfileSchema,
    CareerReportSchema,
    RoleTemplateSchema,
    TargetRoleSchema,
    UpdateCareerProfileRequest,
    WeeklyReviewResponse,
)
from app.services.achievement_service import AchievementService
from app.services.career_readiness_service import CareerReadinessService
from app.services.career_skill_matrix_service import CareerSkillMatrixService

RECENT_MILESTONE_LIMIT = 10


class CareerProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Profile -----------------------------------------------------------------

    def get_or_create_profile(self, user_id: str) -> CareerProfile:
        profile = self.db.execute(
            select(CareerProfile).where(CareerProfile.user_id == user_id)
        ).scalar_one_or_none()
        if profile is None:
            profile = CareerProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def get_profile(self, user_id: str) -> CareerProfileSchema:
        return CareerProfileSchema.model_validate(self.get_or_create_profile(user_id))

    def update_profile(self, user_id: str, payload: UpdateCareerProfileRequest) -> CareerProfileSchema:
        profile = self.get_or_create_profile(user_id)
        if payload.headline is not None:
            profile.headline = payload.headline
        if payload.summary is not None:
            profile.summary = payload.summary
        if payload.primary_target_role_id is not None:
            role = self.db.get(TargetRole, payload.primary_target_role_id)
            if role is None or role.user_id != user_id:
                raise NotFoundError("Target role was not found.")
            profile.primary_target_role_id = payload.primary_target_role_id
        self.db.commit()
        self.db.refresh(profile)
        return CareerProfileSchema.model_validate(profile)

    # --- Role templates ------------------------------------------------------------

    def list_role_templates(self) -> list[RoleTemplateSchema]:
        rows = self.db.execute(
            select(RoleTemplate).where(RoleTemplate.is_active.is_(True)).order_by(RoleTemplate.title)
        ).scalars().all()
        return [RoleTemplateSchema.model_validate(r) for r in rows]

    # --- Target roles ----------------------------------------------------------------

    def list_target_roles(self, user_id: str) -> list[TargetRoleSchema]:
        rows = self.db.execute(
            select(TargetRole).where(TargetRole.user_id == user_id).order_by(TargetRole.created_at)
        ).scalars().all()
        return [TargetRoleSchema.model_validate(r) for r in rows]

    def create_target_role(
        self, user_id: str, *, role_template_slug: str | None, custom_title: str | None, notes: str | None,
        is_primary: bool,
    ) -> TargetRoleSchema:
        role_template = None
        if role_template_slug:
            role_template = self.db.execute(
                select(RoleTemplate).where(RoleTemplate.slug == role_template_slug)
            ).scalar_one_or_none()
            if role_template is None:
                raise NotFoundError(f"Role template '{role_template_slug}' was not found.")

        target_role = TargetRole(
            user_id=user_id,
            role_template_id=role_template.id if role_template else None,
            custom_title=custom_title,
            notes=notes,
            is_primary=is_primary,
        )
        self.db.add(target_role)
        self.db.flush()

        if is_primary:
            profile = self.get_or_create_profile(user_id)
            profile.primary_target_role_id = target_role.id

        self.db.commit()
        self.db.refresh(target_role)
        return TargetRoleSchema.model_validate(target_role)

    def delete_target_role(self, user_id: str, target_role_id: str) -> None:
        role = self.db.get(TargetRole, target_role_id)
        if role is None or role.user_id != user_id:
            raise NotFoundError("Target role was not found.")
        self.db.delete(role)
        self.db.commit()

    # --- Dashboard --------------------------------------------------------------------

    def get_dashboard(self, user_id: str) -> CareerDashboardSchema:
        profile = self.get_or_create_profile(user_id)
        target_roles = self.list_target_roles(user_id)
        primary = next((r for r in target_roles if r.id == profile.primary_target_role_id), None)

        latest_assessment = CareerReadinessService(self.db).get_latest(user_id)
        active_goals = self.db.execute(
            select(CareerGoal).where(
                CareerGoal.user_id == user_id, CareerGoal.status == CareerGoalStatus.ACTIVE
            )
        ).scalars().all()
        # sync_milestones() itself now syncs achievements first (see its own
        # comment) -- this module's own docstring already claimed sync
        # happens "opportunistically (from the Career Dashboard)," but that
        # call was never actually wired in, so a newly-earned badge only
        # showed up once a user happened to open the separate Career
        # Analytics achievements panel (the one previous caller of
        # sync_for_user).
        milestones = self.sync_milestones(user_id)
        achievement_count = self.db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        ).scalars().all()
        saved_jobs = self.db.execute(
            select(JobDescription).where(JobDescription.user_id == user_id)
        ).scalars().all()

        return CareerDashboardSchema(
            profile=CareerProfileSchema.model_validate(profile),
            primary_target_role=primary,
            target_role_count=len(target_roles),
            latest_assessment=latest_assessment,
            active_goal_count=len(active_goals),
            recent_milestones=milestones[:RECENT_MILESTONE_LIMIT],
            achievement_count=len(achievement_count),
            saved_job_count=len(saved_jobs),
        )

    # --- Milestones (auto-generated Career Progress Timeline) --------------------------

    def _existing_titles(
        self, user_id: str, milestone_type: CareerMilestoneType
    ) -> set[tuple[str, datetime]]:
        # Keyed on (title, achieved_at), not title alone: a title formatted
        # from a case/interview/project's own name collides across separate
        # real completions of the SAME template (a fully supported retry —
        # CaseService.start_attempt, InterviewService.retry_interview, and
        # ProjectService.create_from_template all allow re-attempting/
        # re-instantiating one a user already completed) even though each
        # completion is a genuinely new, real event. achieved_at is a real
        # timestamp unique to that specific completion, so a true duplicate
        # sync (re-running this for an already-recorded event) still
        # correctly no-ops, while a second, later completion of the same
        # template is correctly recorded as its own milestone.
        rows = self.db.execute(
            select(CareerMilestone.title, CareerMilestone.achieved_at).where(
                CareerMilestone.user_id == user_id, CareerMilestone.milestone_type == milestone_type
            )
        ).all()
        return {(title, achieved_at) for title, achieved_at in rows}

    def sync_milestones(self, user_id: str) -> list[CareerMilestoneSchema]:
        # Achievements are synced FIRST so a badge earned by this same call's
        # other sync steps (e.g. a skill just crossed the mastery threshold)
        # is reflected by _sync_achievement_milestones below in the same
        # pass, not just on the NEXT call to sync_milestones.
        AchievementService(self.db).sync_for_user(user_id)
        self._sync_project_milestones(user_id)
        self._sync_case_milestones(user_id)
        self._sync_interview_milestones(user_id)
        self._sync_mastery_milestones(user_id)
        self._sync_readiness_milestones(user_id)
        self._sync_achievement_milestones(user_id)
        self.db.commit()
        rows = self.db.execute(
            select(CareerMilestone)
            .where(CareerMilestone.user_id == user_id)
            .order_by(CareerMilestone.achieved_at.desc())
        ).scalars().all()
        return [CareerMilestoneSchema.model_validate(r) for r in rows]

    def _sync_project_milestones(self, user_id: str) -> None:
        existing = self._existing_titles(user_id, CareerMilestoneType.PROJECT_COMPLETED)
        rows = self.db.execute(
            select(Project).where(
                Project.user_id == user_id, Project.status == CaseAttemptStatus.COMPLETED,
                Project.completed_at.is_not(None),
            )
        ).scalars().all()
        for project in rows:
            title = f"Completed project: {project.name}"
            if (title, project.completed_at) in existing:
                continue
            self.db.add(
                CareerMilestone(
                    user_id=user_id,
                    milestone_type=CareerMilestoneType.PROJECT_COMPLETED,
                    title=title,
                    achieved_at=project.completed_at,
                )
            )

    def _sync_case_milestones(self, user_id: str) -> None:
        existing = self._existing_titles(user_id, CareerMilestoneType.CASE_COMPLETED)
        rows = self.db.execute(
            select(CaseAttempt)
            .options(selectinload(CaseAttempt.case))
            .where(CaseAttempt.user_id == user_id, CaseAttempt.status == CaseAttemptStatus.COMPLETED)
        ).scalars().all()
        for attempt in rows:
            title = f"Completed case study: {attempt.case.title}"
            if attempt.completed_at is None or (title, attempt.completed_at) in existing:
                continue
            self.db.add(
                CareerMilestone(
                    user_id=user_id,
                    milestone_type=CareerMilestoneType.CASE_COMPLETED,
                    title=title,
                    achieved_at=attempt.completed_at,
                )
            )

    def _sync_interview_milestones(self, user_id: str) -> None:
        existing = self._existing_titles(user_id, CareerMilestoneType.INTERVIEW_COMPLETED)
        rows = self.db.execute(
            select(Interview).where(
                Interview.user_id == user_id, Interview.status == InterviewStatus.COMPLETED,
                Interview.completed_at.is_not(None),
            )
        ).scalars().all()
        for interview in rows:
            title = f"Completed interview: {interview.title}"
            if (title, interview.completed_at) in existing:
                continue
            self.db.add(
                CareerMilestone(
                    user_id=user_id,
                    milestone_type=CareerMilestoneType.INTERVIEW_COMPLETED,
                    title=title,
                    achieved_at=interview.completed_at,
                )
            )

    def _sync_mastery_milestones(self, user_id: str) -> None:
        existing = self._existing_titles(user_id, CareerMilestoneType.SKILL_LEVEL_UP)
        rows = self.db.execute(
            select(UserSkill, Skill)
            .join(Skill, Skill.id == UserSkill.skill_id)
            .where(UserSkill.user_id == user_id, UserSkill.mastery_score >= 90)
        ).all()
        for user_skill, skill in rows:
            title = f"Reached {MasteryLevel.MASTERED.value} in {skill.name}"
            if (title, user_skill.updated_at) in existing:
                continue
            self.db.add(
                CareerMilestone(
                    user_id=user_id,
                    milestone_type=CareerMilestoneType.SKILL_LEVEL_UP,
                    title=title,
                    achieved_at=user_skill.updated_at,
                )
            )

    def _sync_readiness_milestones(self, user_id: str) -> None:
        # A "level up" is a genuine NEW PEAK readiness level, not every
        # computed assessment -- readiness fluctuates run to run, so this
        # only records the first time each new-best level is reached,
        # skipping any assessment that ties or regresses relative to the
        # best level already seen (in computed_at order).
        existing = self._existing_titles(user_id, CareerMilestoneType.READINESS_LEVEL_UP)
        assessments = self.db.execute(
            select(CareerAssessment)
            .where(CareerAssessment.user_id == user_id)
            .order_by(CareerAssessment.computed_at)
        ).scalars().all()
        levels = list(CareerReadinessLevel)
        best_rank_so_far = -1
        for assessment in assessments:
            rank = levels.index(assessment.overall_readiness_level)
            if rank <= best_rank_so_far:
                continue
            best_rank_so_far = rank
            title = f"Reached {assessment.overall_readiness_level.value} readiness"
            if (title, assessment.computed_at) in existing:
                continue
            self.db.add(
                CareerMilestone(
                    user_id=user_id,
                    milestone_type=CareerMilestoneType.READINESS_LEVEL_UP,
                    title=title,
                    achieved_at=assessment.computed_at,
                )
            )

    def _sync_achievement_milestones(self, user_id: str) -> None:
        existing = self._existing_titles(user_id, CareerMilestoneType.ACHIEVEMENT_EARNED)
        rows = self.db.execute(
            select(UserAchievement, Achievement)
            .join(Achievement, Achievement.id == UserAchievement.achievement_id)
            .where(UserAchievement.user_id == user_id)
        ).all()
        for user_achievement, achievement in rows:
            title = f"Earned achievement: {achievement.title}"
            if (title, user_achievement.earned_at) in existing:
                continue
            self.db.add(
                CareerMilestone(
                    user_id=user_id,
                    milestone_type=CareerMilestoneType.ACHIEVEMENT_EARNED,
                    title=title,
                    achieved_at=user_achievement.earned_at,
                )
            )

    # --- Weekly review ------------------------------------------------------------------

    def get_weekly_review(self, user_id: str) -> WeeklyReviewResponse:
        now = datetime.now(UTC)
        period_start = now - timedelta(days=7)

        exercises = self.db.execute(
            select(ExerciseAttempt).where(
                ExerciseAttempt.user_id == user_id, ExerciseAttempt.attempted_at >= period_start
            )
        ).scalars().all()
        cases = self.db.execute(
            select(CaseAttempt).where(
                CaseAttempt.user_id == user_id, CaseAttempt.status == CaseAttemptStatus.COMPLETED,
                CaseAttempt.completed_at.is_not(None), CaseAttempt.completed_at >= period_start,
            )
        ).scalars().all()
        projects = self.db.execute(
            select(Project).where(
                Project.user_id == user_id, Project.status == CaseAttemptStatus.COMPLETED,
                Project.completed_at.is_not(None), Project.completed_at >= period_start,
            )
        ).scalars().all()
        interviews = self.db.execute(
            select(Interview).where(
                Interview.user_id == user_id, Interview.status == InterviewStatus.COMPLETED,
                Interview.completed_at.is_not(None), Interview.completed_at >= period_start,
            )
        ).scalars().all()
        milestones = self.db.execute(
            select(CareerMilestone).where(
                CareerMilestone.user_id == user_id, CareerMilestone.achieved_at >= period_start
            ).order_by(CareerMilestone.achieved_at.desc())
        ).scalars().all()

        weak_skills = self.db.execute(
            select(Skill.slug)
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(
                UserSkill.user_id == user_id, UserSkill.questions_attempted > 0, UserSkill.mastery_score < 55
            )
        ).scalars().all()

        return WeeklyReviewResponse(
            period_start=period_start.date(),
            period_end=now.date(),
            exercises_attempted=len(exercises),
            exercises_passed=sum(1 for e in exercises if (e.score or 0) >= 70),
            cases_completed=len(cases),
            projects_completed=len(projects),
            interviews_completed=len(interviews),
            new_milestones=[CareerMilestoneSchema.model_validate(m) for m in milestones],
            weak_skill_slugs=list(weak_skills),
        )

    # --- Career Report (exportable) ------------------------------------------------------

    def get_report(self, user_id: str) -> CareerReportSchema:
        profile = CareerProfileSchema.model_validate(self.get_or_create_profile(user_id))
        target_roles = self.list_target_roles(user_id)
        latest_assessment = CareerReadinessService(self.db).get_latest(user_id)
        matrix = CareerSkillMatrixService(self.db).get_matrix(user_id)
        top_gaps = sorted(
            (e for e in matrix if e.is_gap_for_primary_role), key=lambda e: e.mastery_score
        )[:10]
        active_goals = self.db.execute(
            select(CareerGoal).where(
                CareerGoal.user_id == user_id, CareerGoal.status == CareerGoalStatus.ACTIVE
            )
        ).scalars().all()
        milestones = self.sync_milestones(user_id)  # syncs achievements first -- see its own comment
        achievement_count = len(
            self.db.execute(select(UserAchievement).where(UserAchievement.user_id == user_id)).scalars().all()
        )

        return CareerReportSchema(
            generated_at=datetime.now(UTC),
            profile=profile,
            target_roles=target_roles,
            latest_assessment=latest_assessment,
            top_skill_gaps=top_gaps,
            active_goals=[CareerGoalSchema.model_validate(g) for g in active_goals],
            recent_milestones=milestones[:RECENT_MILESTONE_LIMIT],
            achievement_count=achievement_count,
        )
