"""Workspace/cell CRUD — mirrors app/services/sql_workspace_service.py."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.python_lab import PythonCell, PythonWorkspace
from app.schemas.python_lab import (
    CreatePythonWorkspaceRequest,
    UpdatePythonCellRequest,
    UpdatePythonWorkspaceRequest,
)


class PythonWorkspaceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_workspaces(self, user_id: str) -> list[PythonWorkspace]:
        stmt = (
            select(PythonWorkspace)
            .where(PythonWorkspace.user_id == user_id)
            .order_by(PythonWorkspace.created_at)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_workspace(self, user_id: str, workspace_id: str) -> PythonWorkspace:
        workspace = self.db.get(PythonWorkspace, workspace_id)
        if workspace is None or workspace.user_id != user_id:
            raise NotFoundError(f"Workspace '{workspace_id}' was not found.")
        return workspace

    def create_workspace(self, user_id: str, payload: CreatePythonWorkspaceRequest) -> PythonWorkspace:
        workspace = PythonWorkspace(
            user_id=user_id, name=payload.name, selected_dataset=payload.selected_dataset
        )
        self.db.add(workspace)
        self.db.flush()
        # every workspace starts with one empty cell, ready to type into
        self.db.add(PythonCell(workspace_id=workspace.id, display_order=0, code=payload.starter_code or ""))
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def update_workspace(
        self, user_id: str, workspace_id: str, payload: UpdatePythonWorkspaceRequest
    ) -> PythonWorkspace:
        workspace = self.get_workspace(user_id, workspace_id)
        if payload.name is not None:
            workspace.name = payload.name
        if payload.selected_dataset is not None:
            workspace.selected_dataset = payload.selected_dataset
        if payload.notes is not None:
            workspace.notes = payload.notes
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def delete_workspace(self, user_id: str, workspace_id: str) -> None:
        workspace = self.get_workspace(user_id, workspace_id)
        self.db.delete(workspace)
        self.db.commit()

    # --- Cells ---------------------------------------------------------

    def list_cells(self, user_id: str, workspace_id: str) -> list[PythonCell]:
        self.get_workspace(user_id, workspace_id)  # authorization check
        stmt = (
            select(PythonCell)
            .where(PythonCell.workspace_id == workspace_id)
            .order_by(PythonCell.display_order)
        )
        return list(self.db.execute(stmt).scalars().all())

    def add_cell(self, user_id: str, workspace_id: str, *, code: str = "") -> PythonCell:
        self.get_workspace(user_id, workspace_id)
        max_order = (
            self.db.execute(
                select(PythonCell.display_order)
                .where(PythonCell.workspace_id == workspace_id)
                .order_by(PythonCell.display_order.desc())
            )
            .scalars()
            .first()
        )
        cell = PythonCell(workspace_id=workspace_id, display_order=(max_order or 0) + 1, code=code)
        self.db.add(cell)
        self.db.commit()
        self.db.refresh(cell)
        return cell

    def get_cell(self, user_id: str, workspace_id: str, cell_id: str) -> PythonCell:
        self.get_workspace(user_id, workspace_id)
        cell = self.db.get(PythonCell, cell_id)
        if cell is None or cell.workspace_id != workspace_id:
            raise NotFoundError(f"Cell '{cell_id}' was not found.")
        return cell

    def update_cell(
        self, user_id: str, workspace_id: str, cell_id: str, payload: UpdatePythonCellRequest
    ) -> PythonCell:
        cell = self.get_cell(user_id, workspace_id, cell_id)
        if payload.code is not None:
            cell.code = payload.code
        if payload.display_order is not None:
            cell.display_order = payload.display_order
        self.db.commit()
        self.db.refresh(cell)
        return cell

    def record_cell_result(
        self, user_id: str, workspace_id: str, cell_id: str, result_json: dict
    ) -> PythonCell:
        cell = self.get_cell(user_id, workspace_id, cell_id)
        cell.last_result = result_json
        cell.last_executed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(cell)
        return cell

    def delete_cell(self, user_id: str, workspace_id: str, cell_id: str) -> None:
        cell = self.get_cell(user_id, workspace_id, cell_id)
        self.db.delete(cell)
        self.db.commit()
