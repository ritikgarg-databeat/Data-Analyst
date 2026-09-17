from app.models.ai import (
    AIAuditLog,
    AIConversation,
    AIMessage,
    AIMistakeMemory,
    AISettings,
    AISkillDiagnosis,
    AIUsageCounter,
)
from app.models.assessment import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
)
from app.models.career import (
    Achievement,
    BehavioralStory,
    CareerAssessment,
    CareerGoal,
    CareerMilestone,
    CareerNote,
    CareerProfile,
    JDAnalysis,
    JDRequirement,
    JobDescription,
    JobPreparationWorkspace,
    Portfolio,
    PortfolioItem,
    Resume,
    ResumeEvidence,
    ResumeReview,
    ResumeVersion,
    RoleTemplate,
    SkillGap,
    TargetRole,
    UserAchievement,
)
from app.models.case import Case, CaseAttempt
from app.models.chart import Chart
from app.models.data_model import DataModel, DataModelRelationship, DataModelTable
from app.models.data_quality import DataQualityRule, DataQualityRun
from app.models.dataset import Dataset, DatasetNote, DatasetRelationship, DatasetTable, DatasetVersion
from app.models.dataset_profile import DatasetColumnProfile, DatasetProfile, DatasetQualityReport
from app.models.dbt import DbtRun
from app.models.domain import Domain
from app.models.eda import EdaFinding, EdaWorkspace
from app.models.excel_lab import ExcelExerciseTestResult
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.finding import Evidence, Finding, Hypothesis
from app.models.interview import (
    Interview,
    InterviewBookmark,
    InterviewNote,
    InterviewPlan,
    InterviewQuestion,
    InterviewQuestionAttempt,
    InterviewSection,
    InterviewTemplate,
    ReadinessSnapshot,
)
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.lesson_relations import (
    LessonDataset,
    LessonPrerequisite,
    LessonSkill,
    ModulePrerequisite,
    RelatedLesson,
)
from app.models.metric import MetricDefinition
from app.models.module import Module
from app.models.project import Project, ProjectArtifact, ProjectDataset, ProjectMilestone, ProjectTemplate
from app.models.python_lab import (
    PythonCell,
    PythonExecution,
    PythonExerciseTestResult,
    PythonRuntime,
    PythonWorkspace,
)
from app.models.skill import Skill
from app.models.sql_lab import (
    SqlExerciseTestResult,
    SqlQueryHistory,
    SqlSavedQuery,
    SqlTable,
    SqlWorkspace,
)
from app.models.tag import DatasetTag, ExerciseTag, LessonTag, Tag
from app.models.user import User
from app.models.user_skill import UserSkill

__all__ = [
    "Achievement",
    "AIAuditLog",
    "AIConversation",
    "AIMessage",
    "AIMistakeMemory",
    "AISettings",
    "AISkillDiagnosis",
    "AIUsageCounter",
    "Assessment",
    "AssessmentAnswer",
    "AssessmentAttempt",
    "AssessmentQuestion",
    "BehavioralStory",
    "Case",
    "CaseAttempt",
    "CareerAssessment",
    "CareerGoal",
    "CareerMilestone",
    "CareerNote",
    "CareerProfile",
    "Chart",
    "DataModel",
    "DataModelRelationship",
    "DataModelTable",
    "DataQualityRule",
    "DataQualityRun",
    "Dataset",
    "DatasetColumnProfile",
    "DatasetNote",
    "DatasetProfile",
    "DatasetQualityReport",
    "DatasetRelationship",
    "DatasetTable",
    "DatasetTag",
    "DatasetVersion",
    "DbtRun",
    "Domain",
    "EdaFinding",
    "EdaWorkspace",
    "ExcelExerciseTestResult",
    "Evidence",
    "Exercise",
    "ExerciseAttempt",
    "ExerciseTag",
    "Finding",
    "Hypothesis",
    "Interview",
    "InterviewBookmark",
    "InterviewNote",
    "InterviewPlan",
    "InterviewQuestion",
    "InterviewQuestionAttempt",
    "InterviewSection",
    "InterviewTemplate",
    "JDAnalysis",
    "JDRequirement",
    "JobDescription",
    "JobPreparationWorkspace",
    "Lesson",
    "LessonDataset",
    "LessonPrerequisite",
    "LessonProgress",
    "LessonSkill",
    "LessonTag",
    "MetricDefinition",
    "Module",
    "ModulePrerequisite",
    "Portfolio",
    "PortfolioItem",
    "Project",
    "ProjectArtifact",
    "ProjectDataset",
    "ProjectMilestone",
    "ProjectTemplate",
    "PythonCell",
    "PythonExecution",
    "PythonExerciseTestResult",
    "PythonRuntime",
    "PythonWorkspace",
    "ReadinessSnapshot",
    "RelatedLesson",
    "Resume",
    "ResumeEvidence",
    "ResumeReview",
    "ResumeVersion",
    "RoleTemplate",
    "Skill",
    "SkillGap",
    "SqlExerciseTestResult",
    "SqlQueryHistory",
    "SqlSavedQuery",
    "SqlTable",
    "SqlWorkspace",
    "Tag",
    "TargetRole",
    "User",
    "UserAchievement",
    "UserSkill",
]
