from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import (
    get_achievement_service,
    get_ai_career_service,
    get_behavioral_story_service,
    get_career_goal_service,
    get_career_note_service,
    get_career_profile_service,
    get_career_readiness_service,
    get_career_skill_matrix_service,
)
from app.schemas.ai import AIChatResponse, CareerCoachRequest
from app.schemas.career import (
    AchievementSchema,
    BehavioralStorySchema,
    CareerAssessmentSchema,
    CareerDashboardSchema,
    CareerGoalSchema,
    CareerMilestoneSchema,
    CareerNoteSchema,
    CareerProfileSchema,
    CareerReportSchema,
    CareerSkillMatrixEntrySchema,
    ComputeCareerAssessmentRequest,
    CreateBehavioralStoryRequest,
    CreateCareerGoalRequest,
    CreateCareerNoteRequest,
    CreateTargetRoleRequest,
    RoleTemplateSchema,
    StoryCoverageResponse,
    TargetRoleSchema,
    UpdateBehavioralStoryRequest,
    UpdateCareerGoalRequest,
    UpdateCareerNoteRequest,
    UpdateCareerProfileRequest,
    UserAchievementSchema,
    WeeklyReviewResponse,
)
from app.services.achievement_service import AchievementService
from app.services.ai_career_service import AICareerService
from app.services.behavioral_story_service import BehavioralStoryService
from app.services.career_goal_service import CareerGoalService
from app.services.career_note_service import CareerNoteService
from app.services.career_profile_service import CareerProfileService
from app.services.career_readiness_service import CareerReadinessService
from app.services.career_skill_matrix_service import CareerSkillMatrixService

router = APIRouter(prefix="/career", tags=["career"])

ProfileServiceDep = Annotated[CareerProfileService, Depends(get_career_profile_service)]
GoalServiceDep = Annotated[CareerGoalService, Depends(get_career_goal_service)]
ReadinessServiceDep = Annotated[CareerReadinessService, Depends(get_career_readiness_service)]
SkillMatrixServiceDep = Annotated[CareerSkillMatrixService, Depends(get_career_skill_matrix_service)]
AchievementServiceDep = Annotated[AchievementService, Depends(get_achievement_service)]
StoryServiceDep = Annotated[BehavioralStoryService, Depends(get_behavioral_story_service)]
NoteServiceDep = Annotated[CareerNoteService, Depends(get_career_note_service)]
AICareerServiceDep = Annotated[AICareerService, Depends(get_ai_career_service)]


# --- Dashboard ----------------------------------------------------------------


@router.get("/dashboard", response_model=CareerDashboardSchema)
def get_dashboard(user_id: CurrentUserId, service: ProfileServiceDep) -> CareerDashboardSchema:
    return service.get_dashboard(user_id)


@router.get("/weekly-review", response_model=WeeklyReviewResponse)
def get_weekly_review(user_id: CurrentUserId, service: ProfileServiceDep) -> WeeklyReviewResponse:
    return service.get_weekly_review(user_id)


@router.get("/report", response_model=CareerReportSchema)
def get_career_report(user_id: CurrentUserId, service: ProfileServiceDep) -> CareerReportSchema:
    return service.get_report(user_id)


# --- Profile --------------------------------------------------------------------


@router.get("/profile", response_model=CareerProfileSchema)
def get_profile(user_id: CurrentUserId, service: ProfileServiceDep) -> CareerProfileSchema:
    return service.get_profile(user_id)


@router.patch("/profile", response_model=CareerProfileSchema)
def update_profile(
    payload: UpdateCareerProfileRequest, user_id: CurrentUserId, service: ProfileServiceDep
) -> CareerProfileSchema:
    return service.update_profile(user_id, payload)


# --- Role templates + target roles ------------------------------------------------


@router.get("/role-templates", response_model=list[RoleTemplateSchema])
def list_role_templates(service: ProfileServiceDep) -> list[RoleTemplateSchema]:
    return service.list_role_templates()


@router.get("/target-roles", response_model=list[TargetRoleSchema])
def list_target_roles(user_id: CurrentUserId, service: ProfileServiceDep) -> list[TargetRoleSchema]:
    return service.list_target_roles(user_id)


@router.post("/target-roles", response_model=TargetRoleSchema, status_code=201)
def create_target_role(
    payload: CreateTargetRoleRequest, user_id: CurrentUserId, service: ProfileServiceDep
) -> TargetRoleSchema:
    return service.create_target_role(
        user_id,
        role_template_slug=payload.role_template_slug,
        custom_title=payload.custom_title,
        notes=payload.notes,
        is_primary=payload.is_primary,
    )


@router.delete("/target-roles/{target_role_id}", status_code=204)
def delete_target_role(target_role_id: str, user_id: CurrentUserId, service: ProfileServiceDep) -> None:
    service.delete_target_role(user_id, target_role_id)


# --- Readiness assessment ---------------------------------------------------------


@router.get("/readiness/latest", response_model=CareerAssessmentSchema | None)
def get_latest_assessment(
    user_id: CurrentUserId, service: ReadinessServiceDep
) -> CareerAssessmentSchema | None:
    return service.get_latest(user_id)


@router.get("/readiness/history", response_model=list[CareerAssessmentSchema])
def get_assessment_history(
    user_id: CurrentUserId, service: ReadinessServiceDep
) -> list[CareerAssessmentSchema]:
    return service.get_history(user_id)


@router.post("/readiness/compute", response_model=CareerAssessmentSchema, status_code=201)
def compute_assessment(
    payload: ComputeCareerAssessmentRequest, user_id: CurrentUserId, service: ReadinessServiceDep
) -> CareerAssessmentSchema:
    return service.compute(user_id, target_role_id=payload.target_role_id)


# --- Skill matrix ------------------------------------------------------------------


@router.get("/skill-matrix", response_model=list[CareerSkillMatrixEntrySchema])
def get_skill_matrix(
    user_id: CurrentUserId, service: SkillMatrixServiceDep
) -> list[CareerSkillMatrixEntrySchema]:
    return service.get_matrix(user_id)


# --- Goals + timeline --------------------------------------------------------------


@router.get("/goals", response_model=list[CareerGoalSchema])
def list_goals(user_id: CurrentUserId, service: GoalServiceDep) -> list[CareerGoalSchema]:
    return service.list_goals(user_id)


@router.post("/goals", response_model=CareerGoalSchema, status_code=201)
def create_goal(
    payload: CreateCareerGoalRequest, user_id: CurrentUserId, service: GoalServiceDep
) -> CareerGoalSchema:
    return service.create_goal(user_id, payload)


@router.patch("/goals/{goal_id}", response_model=CareerGoalSchema)
def update_goal(
    goal_id: str, payload: UpdateCareerGoalRequest, user_id: CurrentUserId, service: GoalServiceDep
) -> CareerGoalSchema:
    return service.update_goal(user_id, goal_id, payload)


@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: str, user_id: CurrentUserId, service: GoalServiceDep) -> None:
    service.delete_goal(user_id, goal_id)


@router.get("/timeline", response_model=list[CareerMilestoneSchema])
def get_timeline(user_id: CurrentUserId, service: ProfileServiceDep) -> list[CareerMilestoneSchema]:
    return service.sync_milestones(user_id)


# --- Achievements --------------------------------------------------------------------


@router.get("/achievements", response_model=list[AchievementSchema])
def list_all_achievements(service: AchievementServiceDep) -> list[AchievementSchema]:
    return service.list_achievements()


@router.get("/achievements/earned", response_model=list[UserAchievementSchema])
def list_earned_achievements(
    user_id: CurrentUserId, service: AchievementServiceDep
) -> list[UserAchievementSchema]:
    return service.sync_for_user(user_id)


# --- Behavioral Story Bank ------------------------------------------------------------


@router.get("/behavioral-stories", response_model=list[BehavioralStorySchema])
def list_stories(user_id: CurrentUserId, service: StoryServiceDep) -> list[BehavioralStorySchema]:
    return service.list_stories(user_id)


@router.post("/behavioral-stories", response_model=BehavioralStorySchema, status_code=201)
def create_story(
    payload: CreateBehavioralStoryRequest, user_id: CurrentUserId, service: StoryServiceDep
) -> BehavioralStorySchema:
    return service.create_story(user_id, payload)


@router.patch("/behavioral-stories/{story_id}", response_model=BehavioralStorySchema)
def update_story(
    story_id: str, payload: UpdateBehavioralStoryRequest, user_id: CurrentUserId, service: StoryServiceDep
) -> BehavioralStorySchema:
    return service.update_story(user_id, story_id, payload)


@router.delete("/behavioral-stories/{story_id}", status_code=204)
def delete_story(story_id: str, user_id: CurrentUserId, service: StoryServiceDep) -> None:
    service.delete_story(user_id, story_id)


@router.post("/behavioral-stories/{story_id}/practice", response_model=BehavioralStorySchema)
def mark_story_practiced(
    story_id: str, user_id: CurrentUserId, service: StoryServiceDep
) -> BehavioralStorySchema:
    return service.mark_practiced(user_id, story_id)


@router.get("/behavioral-stories/coverage", response_model=StoryCoverageResponse)
def get_story_coverage(user_id: CurrentUserId, service: StoryServiceDep) -> StoryCoverageResponse:
    return service.get_coverage(user_id)


# --- Career Knowledge Base -------------------------------------------------------------


@router.get("/notes", response_model=list[CareerNoteSchema])
def list_notes(
    user_id: CurrentUserId, service: NoteServiceDep, q: str | None = None
) -> list[CareerNoteSchema]:
    return service.list_notes(user_id, query=q)


@router.post("/notes", response_model=CareerNoteSchema, status_code=201)
def create_note(
    payload: CreateCareerNoteRequest, user_id: CurrentUserId, service: NoteServiceDep
) -> CareerNoteSchema:
    return service.create_note(user_id, payload)


@router.patch("/notes/{note_id}", response_model=CareerNoteSchema)
def update_note(
    note_id: str, payload: UpdateCareerNoteRequest, user_id: CurrentUserId, service: NoteServiceDep
) -> CareerNoteSchema:
    return service.update_note(user_id, note_id, payload)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: str, user_id: CurrentUserId, service: NoteServiceDep) -> None:
    service.delete_note(user_id, note_id)


# --- AI Career Coach ---------------------------------------------------------------------


@router.post("/coach", response_model=AIChatResponse)
def ask_career_coach(
    payload: CareerCoachRequest,
    user_id: CurrentUserId,
    ai_service: AICareerServiceDep,
    readiness_service: ReadinessServiceDep,
    goal_service: GoalServiceDep,
) -> AIChatResponse:
    latest_assessment = readiness_service.get_latest(user_id)
    context: dict = {
        "latest_assessment": latest_assessment.model_dump(mode="json") if latest_assessment else None,
        "active_goals": [g.model_dump(mode="json") for g in goal_service.list_goals(user_id)],
    }
    return ai_service.career_coach(
        user_id, message=payload.message, topic=payload.topic, career_context=context,
        conversation_id=payload.conversation_id,
    )
