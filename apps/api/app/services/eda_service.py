"""EDA workspaces (sections 19-21, 50-51 of the Phase 5 spec) — persistence
of a user's exploration state/findings, plus the automatic overview and
question generator built on top of app/dataset_hub/eda_engine.py."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.dataset_hub import eda_engine
from app.models.dataset import Dataset
from app.models.dataset_profile import DatasetProfile
from app.models.eda import EdaFinding, EdaWorkspace
from app.repositories.dataset import DatasetRepository
from app.schemas.eda import (
    CreateEdaWorkspaceRequest,
    CreateFindingRequest,
    EdaFindingSchema,
    EdaOverview,
    EdaQuestion,
    EdaWorkspaceSchema,
    UpdateEdaWorkspaceRequest,
)
from app.sql.paths import resolve_repo_path


class EdaService:
    def __init__(self, db: Session, user_id: str | None = None) -> None:
        self.db = db
        self.dataset_repo = DatasetRepository(db)
        self.user_id = user_id

    # --- Workspaces -----------------------------------------------------

    def list_workspaces(self, user_id: str) -> list[EdaWorkspaceSchema]:
        stmt = (
            select(EdaWorkspace)
            .where(EdaWorkspace.user_id == user_id)
            .order_by(EdaWorkspace.updated_at.desc())
        )
        return [EdaWorkspaceSchema.model_validate(w) for w in self.db.execute(stmt).scalars().all()]

    def _find_dataset(self, dataset_id: str) -> Dataset:
        dataset = self.dataset_repo.get_by_id(dataset_id) or self.dataset_repo.get_by_slug(dataset_id)
        if dataset is None or (
            self.user_id is not None
            and dataset.owner_user_id is not None
            and dataset.owner_user_id != self.user_id
        ):
            raise NotFoundError(f"Dataset '{dataset_id}' was not found.")
        return dataset

    def create_workspace(self, user_id: str, payload: CreateEdaWorkspaceRequest) -> EdaWorkspaceSchema:
        dataset = self._find_dataset(payload.dataset_id)
        table_name = payload.table_name or (dataset.tables[0].table_name if dataset.tables else None)
        workspace = EdaWorkspace(
            user_id=user_id, dataset_id=dataset.id, name=payload.name, table_name=table_name
        )
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return EdaWorkspaceSchema.model_validate(workspace)

    def _find_workspace(self, user_id: str, workspace_id: str) -> EdaWorkspace:
        workspace = self.db.get(EdaWorkspace, workspace_id)
        if workspace is None or workspace.user_id != user_id:
            raise NotFoundError(f"EDA workspace '{workspace_id}' was not found.")
        return workspace

    def get_workspace(self, user_id: str, workspace_id: str) -> EdaWorkspaceSchema:
        return EdaWorkspaceSchema.model_validate(self._find_workspace(user_id, workspace_id))

    def update_workspace(
        self, user_id: str, workspace_id: str, payload: UpdateEdaWorkspaceRequest
    ) -> EdaWorkspaceSchema:
        workspace = self._find_workspace(user_id, workspace_id)
        if payload.name is not None:
            workspace.name = payload.name
        if payload.table_name is not None:
            workspace.table_name = payload.table_name
        if payload.state is not None:
            workspace.state = payload.state
        self.db.commit()
        self.db.refresh(workspace)
        return EdaWorkspaceSchema.model_validate(workspace)

    def delete_workspace(self, user_id: str, workspace_id: str) -> None:
        workspace = self._find_workspace(user_id, workspace_id)
        self.db.delete(workspace)
        self.db.commit()

    # --- Findings -----------------------------------------------------

    def add_finding(self, user_id: str, workspace_id: str, payload: CreateFindingRequest) -> EdaFindingSchema:
        workspace = self._find_workspace(user_id, workspace_id)
        finding = EdaFinding(
            workspace_id=workspace.id,
            observation=payload.observation,
            evidence=payload.evidence,
            business_implication=payload.business_implication,
            recommended_action=payload.recommended_action,
        )
        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)
        return EdaFindingSchema.model_validate(finding)

    def delete_finding(self, user_id: str, workspace_id: str, finding_id: str) -> None:
        self._find_workspace(user_id, workspace_id)
        finding = self.db.get(EdaFinding, finding_id)
        if finding is None or finding.workspace_id != workspace_id:
            raise NotFoundError(f"Finding '{finding_id}' was not found.")
        self.db.delete(finding)
        self.db.commit()

    # --- Overview / questions -------------------------------------------

    def _latest_profile(self, dataset_id: str, table_name: str) -> DatasetProfile:
        stmt = (
            select(DatasetProfile)
            .where(DatasetProfile.dataset_id == dataset_id, DatasetProfile.table_name == table_name)
            .order_by(DatasetProfile.generated_at.desc())
        )
        profile = self.db.execute(stmt).scalars().first()
        if profile is None:
            raise AppError(f"Table '{table_name}' has not been profiled yet.")
        return profile

    def _resolve_table_name(self, dataset: Dataset, table_name: str | None) -> str:
        if table_name:
            return table_name
        if not dataset.tables:
            raise AppError(f"Dataset '{dataset.slug}' has no tables yet.")
        return dataset.tables[0].table_name

    def dataset_overview(self, dataset_id: str, table_name: str | None) -> EdaOverview:
        dataset = self._find_dataset(dataset_id)
        resolved_table = self._resolve_table_name(dataset, table_name)
        profile = self._latest_profile(dataset.id, resolved_table)
        dataset_table = next(t for t in dataset.tables if t.table_name == resolved_table)
        overview = eda_engine.build_overview(profile, resolve_repo_path(dataset_table.file_path))
        return EdaOverview(**overview)

    def dataset_questions(self, dataset_id: str, table_name: str | None) -> list[EdaQuestion]:
        dataset = self._find_dataset(dataset_id)
        resolved_table = self._resolve_table_name(dataset, table_name)
        profile = self._latest_profile(dataset.id, resolved_table)
        return [EdaQuestion(**q) for q in eda_engine.generate_questions(profile)]

    def generate_workspace_overview(self, user_id: str, workspace_id: str) -> EdaOverview:
        workspace = self._find_workspace(user_id, workspace_id)
        overview = self.dataset_overview(workspace.dataset_id, workspace.table_name)
        workspace.overview = overview.model_dump(mode="json")
        self.db.commit()
        return overview

    def workspace_questions(self, user_id: str, workspace_id: str) -> list[EdaQuestion]:
        workspace = self._find_workspace(user_id, workspace_id)
        return self.dataset_questions(workspace.dataset_id, workspace.table_name)
