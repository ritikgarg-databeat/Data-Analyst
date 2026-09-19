"""Project Engine — the Phase 5 minimal shell (CRUD + "create from dataset")
extended in place (Phase 8, spec sections 29-40) with milestones, artifacts,
dataset usage, documentation/presentation, template instantiation, and
rubric-based submission. Submission reuses `app/case_engine/grading.py`'s
pure `score_rubric`/`build_feedback` exactly like
`app/services/case_service.py`'s `submit_attempt` — same instant
SUBMITTED->COMPLETED convention, same "no objective signal -> self-assessed"
fallback (ProjectTemplate has no `required_exercise_slugs` concept, so
`technical_pct` is always `None` here, and `score_rubric` falls back to
self-assessment for every category, `is_technical` included)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.case_engine.feedback import Feedback, build_feedback
from app.case_engine.grading import ScoreResult, score_rubric
from app.core.errors import AppError, NotFoundError
from app.models.chart import Chart
from app.models.data_model import DataModel
from app.models.dataset import Dataset
from app.models.enums import CaseAttemptStatus, ProjectArtifactType
from app.models.project import Project as ProjectModel
from app.models.project import ProjectArtifact, ProjectDataset, ProjectMilestone, ProjectTemplate
from app.models.python_lab import PythonExecution
from app.models.sql_lab import SqlQueryHistory
from app.repositories.dataset import DatasetRepository
from app.schemas.project import (
    CreateProjectFromDatasetRequest,
    CreateProjectRequest,
    Project,
    ProjectTemplateSchema,
    UpdateProjectRequest,
)


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.dataset_repo = DatasetRepository(db)

    def _find_dataset(self, user_id: str, dataset_id: str) -> Dataset:
        dataset = self.dataset_repo.get_by_id(dataset_id) or self.dataset_repo.get_by_slug(dataset_id)
        if dataset is None or (dataset.owner_user_id is not None and dataset.owner_user_id != user_id):
            raise NotFoundError(f"Dataset '{dataset_id}' was not found.")
        return dataset

    # --- Phase 5: free-form project shell -----------------------------------

    def list_projects(self, user_id: str) -> list[Project]:
        stmt = (
            select(ProjectModel)
            .where(ProjectModel.user_id == user_id)
            .order_by(ProjectModel.updated_at.desc())
        )
        return [Project.model_validate(p) for p in self.db.execute(stmt).scalars().all()]

    def create(self, user_id: str, payload: CreateProjectRequest) -> Project:
        dataset_id = None
        if payload.dataset_id is not None:
            dataset_id = self._find_dataset(user_id, payload.dataset_id).id
        project = ProjectModel(
            user_id=user_id, dataset_id=dataset_id, name=payload.name, description=payload.description
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    def create_from_dataset(
        self, user_id: str, dataset_id: str, payload: CreateProjectFromDatasetRequest
    ) -> Project:
        dataset = self._find_dataset(user_id, dataset_id)
        project = ProjectModel(
            user_id=user_id,
            dataset_id=dataset.id,
            name=payload.name or f"{dataset.name} project",
            description=payload.description or f"A project shell built on the '{dataset.name}' dataset.",
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    def _find(self, user_id: str, project_id: str) -> ProjectModel:
        project = self.db.get(ProjectModel, project_id)
        if project is None or project.user_id != user_id:
            raise NotFoundError(f"Project '{project_id}' was not found.")
        return project

    def get(self, user_id: str, project_id: str) -> Project:
        return Project.model_validate(self._find(user_id, project_id))

    def update(self, user_id: str, project_id: str, payload: UpdateProjectRequest) -> Project:
        project = self._find(user_id, project_id)
        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.notes is not None:
            project.notes = payload.notes
        if payload.status is not None:
            project.status = payload.status
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    def delete(self, user_id: str, project_id: str) -> None:
        project = self._find(user_id, project_id)
        self.db.delete(project)
        self.db.commit()

    # --- Phase 8: templates --------------------------------------------------

    def list_templates(self) -> list[ProjectTemplateSchema]:
        stmt = (
            select(ProjectTemplate).where(ProjectTemplate.is_active.is_(True)).order_by(ProjectTemplate.title)
        )
        return [ProjectTemplateSchema.model_validate(t) for t in self.db.execute(stmt).scalars().all()]

    def list_templates_admin(self) -> list[ProjectTemplate]:
        stmt = select(ProjectTemplate).order_by(ProjectTemplate.title)
        return list(self.db.execute(stmt).scalars().all())

    def update_template_admin(self, template_id: str, is_active: bool) -> ProjectTemplate:
        template = self.db.get(ProjectTemplate, template_id)
        if template is None:
            raise NotFoundError(f"Project template '{template_id}' not found.")
        template.is_active = is_active
        self.db.commit()
        self.db.refresh(template)
        return template

    def _get_template_by_slug(self, slug: str) -> ProjectTemplate:
        template = self.db.execute(
            select(ProjectTemplate).where(ProjectTemplate.slug == slug)
        ).scalar_one_or_none()
        if template is None or not template.is_active:
            raise NotFoundError(f"Project template '{slug}' not found.")
        return template

    def get_template(self, slug: str) -> ProjectTemplateSchema:
        return ProjectTemplateSchema.model_validate(self._get_template_by_slug(slug))

    def create_from_template(self, user_id: str, template_slug: str) -> Project:
        template = self._get_template_by_slug(template_slug)
        project = ProjectModel(
            user_id=user_id,
            template_id=template.id,
            name=template.title,
            description=template.objective,
            objective=template.objective,
            business_context=template.business_context,
            requirements=list(template.requirements),
            status=CaseAttemptStatus.IN_PROGRESS,
            started_at=datetime.now(UTC),
        )
        self.db.add(project)
        self.db.flush()  # assign project.id before inserting milestone rows
        for i, milestone in enumerate(template.milestones):
            self.db.add(
                ProjectMilestone(
                    project_id=project.id,
                    title=milestone["title"],
                    description=milestone.get("description"),
                    display_order=i,
                )
            )
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    # --- Milestones ------------------------------------------------------------

    def _find_milestone(self, user_id: str, project_id: str, milestone_id: str) -> ProjectMilestone:
        project = self._find(user_id, project_id)
        milestone = self.db.get(ProjectMilestone, milestone_id)
        if milestone is None or milestone.project_id != project.id:
            raise NotFoundError(f"Milestone '{milestone_id}' not found.")
        return milestone

    def update_milestone(
        self, user_id: str, project_id: str, milestone_id: str, is_completed: bool
    ) -> Project:
        milestone = self._find_milestone(user_id, project_id, milestone_id)
        milestone.is_completed = is_completed
        milestone.completed_at = datetime.now(UTC) if is_completed else None
        self.db.commit()
        project = self._find(user_id, project_id)
        self.db.refresh(project)
        return Project.model_validate(project)

    # --- Artifacts ------------------------------------------------------------

    def add_artifact(
        self,
        user_id: str,
        project_id: str,
        *,
        artifact_type: ProjectArtifactType,
        ref_id: str | None,
        label: str,
        snapshot: str | None,
        notes: str | None,
    ) -> ProjectArtifact:
        project = self._find(user_id, project_id)
        # Existing projects historically allowed descriptive, dangling ref
        # ids. Keep that compatibility, but never let a real row owned by a
        # different account be attached through a raw id.
        referenced_models = {
            ProjectArtifactType.SQL_QUERY: SqlQueryHistory,
            ProjectArtifactType.PYTHON_EXECUTION: PythonExecution,
            ProjectArtifactType.CHART: Chart,
            ProjectArtifactType.DATA_MODEL: DataModel,
        }
        model = referenced_models.get(artifact_type)
        if ref_id and model is not None:
            referenced = self.db.get(model, ref_id)
            if referenced is not None and referenced.user_id != user_id:
                raise NotFoundError(f"Artifact reference '{ref_id}' not found.")
        artifact = ProjectArtifact(
            project_id=project.id,
            artifact_type=artifact_type,
            ref_id=ref_id,
            label=label,
            snapshot=snapshot,
            notes=notes,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def delete_artifact(self, user_id: str, project_id: str, artifact_id: str) -> None:
        project = self._find(user_id, project_id)
        artifact = self.db.get(ProjectArtifact, artifact_id)
        if artifact is None or artifact.project_id != project.id:
            raise NotFoundError(f"Artifact '{artifact_id}' not found.")
        self.db.delete(artifact)
        self.db.commit()

    # --- Dataset usage ----------------------------------------------------------

    def add_dataset(
        self, user_id: str, project_id: str, dataset_id: str, reason: str | None
    ) -> ProjectDataset:
        project = self._find(user_id, project_id)
        dataset = self._find_dataset(user_id, dataset_id)
        project_dataset = ProjectDataset(project_id=project.id, dataset_id=dataset.id, reason=reason)
        self.db.add(project_dataset)
        self.db.commit()
        self.db.refresh(project_dataset)
        return project_dataset

    def remove_dataset(self, user_id: str, project_id: str, project_dataset_id: str) -> None:
        project = self._find(user_id, project_id)
        project_dataset = self.db.get(ProjectDataset, project_dataset_id)
        if project_dataset is None or project_dataset.project_id != project.id:
            raise NotFoundError(f"Project dataset '{project_dataset_id}' not found.")
        self.db.delete(project_dataset)
        self.db.commit()

    # --- Documentation / presentation / linking ---------------------------------

    def update_documentation(self, user_id: str, project_id: str, documentation: dict) -> Project:
        project = self._find(user_id, project_id)
        project.documentation = documentation
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    def update_presentation(self, user_id: str, project_id: str, presentation: list[dict]) -> Project:
        project = self._find(user_id, project_id)
        project.presentation = presentation
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    def link_data_model(self, user_id: str, project_id: str, data_model_id: str | None) -> Project:
        project = self._find(user_id, project_id)
        if data_model_id is not None:
            data_model = self.db.get(DataModel, data_model_id)
            if data_model is not None and data_model.user_id != user_id:
                raise NotFoundError(f"Data model '{data_model_id}' not found.")
        project.data_model_id = data_model_id
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    def update_dbt_refs(self, user_id: str, project_id: str, dbt_model_refs: list[str]) -> Project:
        project = self._find(user_id, project_id)
        project.dbt_model_refs = dbt_model_refs
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    # --- Submission & grading ----------------------------------------------------

    def submit_project(
        self, user_id: str, project_id: str, rubric_selections: dict[str, list[str]]
    ) -> Project:
        project = self._find(user_id, project_id)
        if project.status == CaseAttemptStatus.COMPLETED:
            raise AppError("This project has already been completed.")
        if project.template_id is None:
            raise AppError("Only projects started from a template can be submitted for rubric scoring.")
        template = self.db.get(ProjectTemplate, project.template_id)
        if template is None:
            raise NotFoundError("The project's template no longer exists.")

        now = datetime.now(UTC)
        project.rubric_selections = rubric_selections

        score_result: ScoreResult = score_rubric(template.rubric, rubric_selections, technical_pct=None)
        feedback: Feedback = build_feedback(score_result)

        project.score = {
            "overall": score_result.overall,
            "categories": [
                {
                    "category": c.category,
                    "weight": c.weight,
                    "earned_points": c.earned_points,
                    "total_points": c.total_points,
                    "pct": c.pct,
                    "is_technical": c.is_technical,
                }
                for c in score_result.categories
            ],
            "feedback": {
                "what_went_well": feedback.what_went_well,
                "what_missed": feedback.what_missed,
                "technical_issues": feedback.technical_issues,
                "business_reasoning_issues": feedback.business_reasoning_issues,
                "communication_issues": feedback.communication_issues,
            },
        }
        # Grading is fully deterministic and instant in this phase, exactly
        # like CaseService.submit_attempt — no UNDER_REVIEW wait.
        project.status = CaseAttemptStatus.COMPLETED
        project.submitted_at = now
        project.completed_at = now
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)

    def save_reflection(self, user_id: str, project_id: str, reflection: dict) -> Project:
        project = self._find(user_id, project_id)
        project.reflection = reflection
        self.db.commit()
        self.db.refresh(project)
        return Project.model_validate(project)
