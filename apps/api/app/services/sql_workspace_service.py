from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.sql_lab import SqlQueryHistory, SqlSavedQuery, SqlWorkspace
from app.schemas.sql import (
    CreateSqlSavedQueryRequest,
    CreateSqlWorkspaceRequest,
    SqlQueryHistoryItem,
    SqlSavedQuerySchema,
    SqlWorkspaceSchema,
    UpdateSqlSavedQueryRequest,
)


class SqlWorkspaceService:
    """CRUD for SqlWorkspace/SqlSavedQuery plus read/delete for SqlQueryHistory.
    Query history rows are written by SqlExecutionService.execute, not here."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- history ---

    def list_history(
        self, user_id: str, *, status: str | None = None, engine: str | None = None, limit: int = 50
    ) -> list[SqlQueryHistoryItem]:
        stmt = select(SqlQueryHistory).where(SqlQueryHistory.user_id == user_id)
        if status:
            stmt = stmt.where(SqlQueryHistory.status == status)
        if engine:
            stmt = stmt.where(SqlQueryHistory.engine == engine)
        stmt = stmt.order_by(SqlQueryHistory.executed_at.desc()).limit(limit)
        rows = self.db.execute(stmt).scalars().all()
        return [SqlQueryHistoryItem.model_validate(r) for r in rows]

    def delete_history_entry(self, user_id: str, history_id: str) -> None:
        entry = self.db.get(SqlQueryHistory, history_id)
        if entry is None or entry.user_id != user_id:
            raise NotFoundError(f"History entry '{history_id}' was not found.")
        self.db.delete(entry)
        self.db.commit()

    # --- workspaces ---

    def list_workspaces(self, user_id: str) -> list[SqlWorkspaceSchema]:
        stmt = select(SqlWorkspace).where(SqlWorkspace.user_id == user_id).order_by(SqlWorkspace.created_at)
        return [SqlWorkspaceSchema.model_validate(w) for w in self.db.execute(stmt).scalars().all()]

    def create_workspace(self, user_id: str, payload: CreateSqlWorkspaceRequest) -> SqlWorkspaceSchema:
        workspace = SqlWorkspace(
            user_id=user_id, name=payload.name, engine=payload.engine, database=payload.database
        )
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return SqlWorkspaceSchema.model_validate(workspace)

    # --- saved queries ---

    def list_saved_queries(self, user_id: str, workspace_id: str | None = None) -> list[SqlSavedQuerySchema]:
        stmt = select(SqlSavedQuery).where(SqlSavedQuery.user_id == user_id)
        if workspace_id:
            stmt = stmt.where(SqlSavedQuery.workspace_id == workspace_id)
        stmt = stmt.order_by(SqlSavedQuery.updated_at.desc())
        return [self._to_saved_schema(q) for q in self.db.execute(stmt).scalars().all()]

    def _to_saved_schema(self, query: SqlSavedQuery) -> SqlSavedQuerySchema:
        return SqlSavedQuerySchema(
            id=query.id,
            workspace_id=query.workspace_id,
            title=query.title,
            description=query.description,
            query=query.query,
            engine=query.engine,
            database=query.database,
            tags=[t.strip() for t in query.tags.split(",") if t.strip()] if query.tags else [],
            created_at=query.created_at,
            updated_at=query.updated_at,
        )

    def create_saved_query(self, user_id: str, payload: CreateSqlSavedQueryRequest) -> SqlSavedQuerySchema:
        saved = SqlSavedQuery(
            user_id=user_id,
            workspace_id=payload.workspace_id,
            title=payload.title,
            description=payload.description,
            query=payload.query,
            engine=payload.engine,
            database=payload.database,
            tags=",".join(payload.tags) if payload.tags else None,
        )
        self.db.add(saved)
        self.db.commit()
        self.db.refresh(saved)
        return self._to_saved_schema(saved)

    def update_saved_query(
        self, user_id: str, query_id: str, payload: UpdateSqlSavedQueryRequest
    ) -> SqlSavedQuerySchema:
        saved = self.db.get(SqlSavedQuery, query_id)
        if saved is None or saved.user_id != user_id:
            raise NotFoundError(f"Saved query '{query_id}' was not found.")
        if payload.title is not None:
            saved.title = payload.title
        if payload.description is not None:
            saved.description = payload.description
        if payload.query is not None:
            saved.query = payload.query
        if payload.workspace_id is not None:
            saved.workspace_id = payload.workspace_id
        if payload.tags is not None:
            saved.tags = ",".join(payload.tags) if payload.tags else None
        self.db.commit()
        self.db.refresh(saved)
        return self._to_saved_schema(saved)

    def delete_saved_query(self, user_id: str, query_id: str) -> None:
        saved = self.db.get(SqlSavedQuery, query_id)
        if saved is None or saved.user_id != user_id:
            raise NotFoundError(f"Saved query '{query_id}' was not found.")
        self.db.delete(saved)
        self.db.commit()
