from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.data_modeling.service import DataModelService
from app.data_quality.service import DataQualityService
from app.dbt_lab.service import DbtLabService
from app.dependencies.current_user import CurrentUserId
from app.dependencies.db import get_db
from app.python_lab.service import PythonExecutionService
from app.services.achievement_service import AchievementService
from app.services.ai_career_service import AICareerService
from app.services.ai_coach_service import AICoachService
from app.services.ai_service import AIService
from app.services.analytics_case_service import AnalyticsCaseService
from app.services.assessment_service import AssessmentService
from app.services.backup_service import BackupService
from app.services.behavioral_story_service import BehavioralStoryService
from app.services.career_goal_service import CareerGoalService
from app.services.career_note_service import CareerNoteService
from app.services.career_profile_service import CareerProfileService
from app.services.career_readiness_service import CareerReadinessService
from app.services.career_skill_matrix_service import CareerSkillMatrixService
from app.services.case_service import CaseService
from app.services.chart_service import ChartService
from app.services.data_integrity_service import DataIntegrityService
from app.services.dataset_analysis_service import DatasetAnalysisService
from app.services.dataset_service import DatasetService
from app.services.dbt_exercise_service import DbtExerciseService
from app.services.domain_service import DomainService
from app.services.eda_service import EdaService
from app.services.excel_exercise_service import ExcelExerciseService
from app.services.exercise_service import ExerciseService
from app.services.finding_service import FindingService
from app.services.interview_question_service import InterviewQuestionService
from app.services.interview_readiness_service import InterviewReadinessService
from app.services.interview_service import InterviewService
from app.services.jd_service import JDService
from app.services.job_ready_checklist_service import JobReadyChecklistService
from app.services.kaggle_service import KaggleService
from app.services.lesson_service import LessonService
from app.services.metrics_service import MetricsService
from app.services.module_service import ModuleService
from app.services.next_best_action_service import NextBestActionService
from app.services.portfolio_service import PortfolioService
from app.services.progress_service import ProgressService
from app.services.project_service import ProjectService
from app.services.python_exercise_service import PythonExerciseService
from app.services.python_workspace_service import PythonWorkspaceService
from app.services.recommendations import RecommendationService
from app.services.resume_service import ResumeService
from app.services.search import SearchService
from app.services.skill_service import SkillService
from app.services.sql_exercise_service import SqlExerciseService
from app.services.sql_workspace_service import SqlWorkspaceService
from app.services.system_health_service import SystemHealthService
from app.services.tag_service import TagService
from app.services.user_service import UserService
from app.sql.service import SqlExecutionService

DbSession = Annotated[Session, Depends(get_db)]


def get_user_service(db: DbSession) -> UserService:
    return UserService(db)


def get_domain_service(db: DbSession) -> DomainService:
    return DomainService(db)


def get_module_service(db: DbSession) -> ModuleService:
    return ModuleService(db)


def get_lesson_service(db: DbSession) -> LessonService:
    return LessonService(db)


def get_skill_service(db: DbSession) -> SkillService:
    return SkillService(db)


def get_progress_service(db: DbSession) -> ProgressService:
    return ProgressService(db)


def get_exercise_service(db: DbSession) -> ExerciseService:
    return ExerciseService(db)


def get_dataset_service(db: DbSession, user_id: CurrentUserId) -> DatasetService:
    return DatasetService(db, user_id=user_id)


def get_tag_service(db: DbSession) -> TagService:
    return TagService(db)


def get_assessment_service(db: DbSession) -> AssessmentService:
    return AssessmentService(db)


def get_search_service(db: DbSession) -> SearchService:
    return SearchService(db)


def get_recommendation_service(db: DbSession) -> RecommendationService:
    return RecommendationService(db)


def get_sql_execution_service(db: DbSession, user_id: CurrentUserId) -> SqlExecutionService:
    return SqlExecutionService(db, user_id=user_id)


def get_sql_exercise_service(db: DbSession) -> SqlExerciseService:
    return SqlExerciseService(db)


def get_sql_workspace_service(db: DbSession) -> SqlWorkspaceService:
    return SqlWorkspaceService(db)


def get_python_execution_service(db: DbSession, user_id: CurrentUserId) -> PythonExecutionService:
    return PythonExecutionService(db, user_id=user_id)


def get_python_exercise_service(db: DbSession, user_id: CurrentUserId) -> PythonExerciseService:
    return PythonExerciseService(db, user_id=user_id)


def get_python_workspace_service(db: DbSession) -> PythonWorkspaceService:
    return PythonWorkspaceService(db)


def get_dataset_analysis_service(db: DbSession, user_id: CurrentUserId) -> DatasetAnalysisService:
    return DatasetAnalysisService(db, user_id=user_id)


def get_kaggle_service(db: DbSession, user_id: CurrentUserId) -> KaggleService:
    return KaggleService(db, user_id=user_id)


def get_eda_service(db: DbSession, user_id: CurrentUserId) -> EdaService:
    return EdaService(db, user_id=user_id)


def get_chart_service(db: DbSession, user_id: CurrentUserId) -> ChartService:
    return ChartService(db, user_id=user_id)


def get_project_service(db: DbSession) -> ProjectService:
    return ProjectService(db)


def get_statistics_service(db: DbSession, user_id: CurrentUserId) -> Any:
    from app.services.statistics_service import StatisticsService

    return StatisticsService(db, user_id=user_id)


def get_experiment_service(db: DbSession) -> Any:
    from app.services.experiment_service import ExperimentService

    return ExperimentService(db)


def get_metrics_service(db: DbSession) -> MetricsService:
    return MetricsService(db)


def get_analytics_case_service(db: DbSession) -> AnalyticsCaseService:
    return AnalyticsCaseService(db)


def get_dbt_lab_service(db: DbSession, user_id: CurrentUserId) -> DbtLabService:
    return DbtLabService(db, user_id=user_id)


def get_dbt_exercise_service(db: DbSession) -> DbtExerciseService:
    return DbtExerciseService(db)


def get_data_quality_service(db: DbSession, user_id: CurrentUserId) -> DataQualityService:
    return DataQualityService(db, user_id=user_id)


def get_data_model_service(db: DbSession) -> DataModelService:
    return DataModelService(db)


def get_case_service(db: DbSession) -> CaseService:
    return CaseService(db)


def get_finding_service(db: DbSession) -> FindingService:
    return FindingService(db)


def get_excel_exercise_service(db: DbSession) -> ExcelExerciseService:
    return ExcelExerciseService(db)


def get_interview_service(db: DbSession) -> InterviewService:
    return InterviewService(db)


def get_interview_question_service(db: DbSession) -> InterviewQuestionService:
    return InterviewQuestionService(db)


def get_interview_readiness_service(db: DbSession) -> InterviewReadinessService:
    return InterviewReadinessService(db)


def get_ai_service(db: DbSession) -> AIService:
    return AIService(db)


def get_ai_coach_service(db: DbSession) -> AICoachService:
    return AICoachService(db)


def get_ai_career_service(db: DbSession) -> AICareerService:
    return AICareerService(db)


def get_career_profile_service(db: DbSession) -> CareerProfileService:
    return CareerProfileService(db)


def get_career_goal_service(db: DbSession) -> CareerGoalService:
    return CareerGoalService(db)


def get_career_readiness_service(db: DbSession) -> CareerReadinessService:
    return CareerReadinessService(db)


def get_career_skill_matrix_service(db: DbSession) -> CareerSkillMatrixService:
    return CareerSkillMatrixService(db)


def get_achievement_service(db: DbSession) -> AchievementService:
    return AchievementService(db)


def get_behavioral_story_service(db: DbSession) -> BehavioralStoryService:
    return BehavioralStoryService(db)


def get_career_note_service(db: DbSession) -> CareerNoteService:
    return CareerNoteService(db)


def get_jd_service(db: DbSession) -> JDService:
    return JDService(db)


def get_resume_service(db: DbSession) -> ResumeService:
    return ResumeService(db)


def get_portfolio_service(db: DbSession) -> PortfolioService:
    return PortfolioService(db)


def get_next_best_action_service(db: DbSession) -> NextBestActionService:
    return NextBestActionService(db)


def get_system_health_service(db: DbSession) -> SystemHealthService:
    return SystemHealthService(db)


def get_backup_service(db: DbSession) -> BackupService:
    return BackupService(db)


def get_data_integrity_service(db: DbSession) -> DataIntegrityService:
    return DataIntegrityService(db)


def get_job_ready_checklist_service(db: DbSession) -> JobReadyChecklistService:
    return JobReadyChecklistService(db)
