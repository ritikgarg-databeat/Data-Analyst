"""System Health / Diagnostics (Phase 12) — the existing `GET /api/v1/health`
endpoint is a pure liveness check (process up? yes/no); this is the
dependency-AWARE check the spec asks for: database, DuckDB, the Python Lab
sandbox, dbt, the AI provider, and Kaggle. Every check is read-only and
side-effect-free (no writes, no container starts) so it's always safe to
call. Local-first by design: AI and Kaggle report `not_configured` rather
than `unavailable` when simply unset — that's expected, not a failure."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime

import duckdb
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.python_lab.service import PythonExecutionService
from app.schemas.platform import ServiceStatusSchema, SystemHealthResponse


class SystemHealthService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def _check_database(self) -> ServiceStatusSchema:
        try:
            self.db.execute(text("SELECT 1"))
            return ServiceStatusSchema(name="Core Database", status="ok")
        except Exception as exc:  # noqa: BLE001 — a diagnostic must never itself crash
            return ServiceStatusSchema(name="Core Database", status="unavailable", detail=str(exc)[:200])

    def _check_duckdb(self) -> ServiceStatusSchema:
        try:
            con = duckdb.connect(":memory:")
            con.execute("SELECT 1")
            con.close()
            return ServiceStatusSchema(name="DuckDB", status="ok")
        except Exception as exc:  # noqa: BLE001
            return ServiceStatusSchema(name="DuckDB", status="unavailable", detail=str(exc)[:200])

    def _check_postgres_sql_lab(self) -> ServiceStatusSchema:
        if not self.settings.sql_lab_postgres_available:
            return ServiceStatusSchema(
                name="SQL Lab — PostgreSQL engine",
                status="not_configured",
                detail="Optional. Set SQL_LAB_POSTGRES_URL to enable a second SQL engine alongside DuckDB.",
            )
        return ServiceStatusSchema(name="SQL Lab — PostgreSQL engine", status="ok")

    def _check_python_sandbox(self) -> ServiceStatusSchema:
        try:
            available, reason = PythonExecutionService(self.db, settings=self.settings).is_available()
        except Exception as exc:  # noqa: BLE001
            return ServiceStatusSchema(name="Python Sandbox", status="unavailable", detail=str(exc)[:200])
        if available:
            return ServiceStatusSchema(name="Python Sandbox", status="ok")
        return ServiceStatusSchema(
            name="Python Sandbox", status="unavailable", detail=reason or "Docker is not reachable."
        )

    def _check_dbt(self) -> ServiceStatusSchema:
        if shutil.which("dbt") is None:
            return ServiceStatusSchema(
                name="dbt", status="unavailable", detail="The `dbt` CLI was not found on PATH."
            )
        return ServiceStatusSchema(name="dbt", status="ok")

    def _check_ai_provider(self) -> ServiceStatusSchema:
        if self.settings.ai_provider == "local":
            return ServiceStatusSchema(
                name="AI Provider",
                status="not_configured",
                detail="Running in local (no-provider) mode. Set AI_PROVIDER and a matching API key to "
                "enable real AI tutoring/coaching.",
            )
        if self.settings.ai_configured:
            return ServiceStatusSchema(
                name="AI Provider", status="ok", detail=f"Provider: {self.settings.ai_provider}"
            )
        return ServiceStatusSchema(
            name="AI Provider",
            status="not_configured",
            detail=(
                f"AI_PROVIDER is set to '{self.settings.ai_provider}' but no matching API key is configured."
            ),
        )

    def _check_kaggle(self) -> ServiceStatusSchema:
        if self.settings.kaggle_configured:
            return ServiceStatusSchema(name="Kaggle", status="ok")
        return ServiceStatusSchema(
            name="Kaggle",
            status="not_configured",
            detail="Optional. Set KAGGLE_USERNAME and KAGGLE_KEY to enable.",
        )

    def check_all(self) -> SystemHealthResponse:
        return SystemHealthResponse(
            checked_at=datetime.now(UTC),
            services=[
                self._check_database(),
                self._check_duckdb(),
                self._check_postgres_sql_lab(),
                self._check_python_sandbox(),
                self._check_dbt(),
                self._check_ai_provider(),
                self._check_kaggle(),
            ],
        )
