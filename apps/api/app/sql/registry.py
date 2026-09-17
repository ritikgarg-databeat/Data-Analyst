"""Resolves engine/database names (as used in the API and URLs) to actual
SqlEngine instances, backed by `Dataset` + `SqlTable` rows for DuckDB and
`Settings.sql_lab_postgres_url` for Postgres.

A DuckDB "database" is just a `Dataset` that has one or more `SqlTable`
children — the dataset itself stays a normal Phase 1/2 `Dataset` row (so it
still shows up in `/datasets`), SqlTable rows are what make it SQL-Lab
queryable.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.dataset import Dataset
from app.models.sql_lab import SqlTable
from app.sql.engines.base import SqlEngine, SqlEngineError
from app.sql.engines.duckdb_engine import DuckDBEngine, DuckDbTableSource
from app.sql.engines.postgres_engine import PostgresEngine
from app.sql.paths import resolve_repo_path

POSTGRES_DATABASE_NAME = "practice"


@dataclass
class EngineInfo:
    name: str
    label: str
    is_available: bool
    reason: str | None = None


@dataclass
class DatabaseInfo:
    name: str
    label: str
    engine: str
    description: str | None
    table_count: int


def list_engines(settings: Settings) -> list[EngineInfo]:
    engines = [EngineInfo(name="duckdb", label="DuckDB", is_available=True)]
    if settings.sql_lab_postgres_available:
        engines.append(EngineInfo(name="postgres", label="PostgreSQL", is_available=True))
    else:
        engines.append(
            EngineInfo(
                name="postgres",
                label="PostgreSQL",
                is_available=False,
                reason="SQL_LAB_POSTGRES_URL is not configured for this installation.",
            )
        )
    return engines


def list_duckdb_databases(db: Session) -> list[DatabaseInfo]:
    stmt = select(Dataset, SqlTable).join(SqlTable, SqlTable.dataset_id == Dataset.id).order_by(Dataset.name)
    rows = db.execute(stmt).all()
    grouped: dict[str, DatabaseInfo] = {}
    for dataset, _table in rows:
        info = grouped.get(dataset.slug)
        if info is None:
            grouped[dataset.slug] = DatabaseInfo(
                name=dataset.slug,
                label=dataset.name,
                engine="duckdb",
                description=dataset.description,
                table_count=1,
            )
        else:
            info.table_count += 1
    return list(grouped.values())


def list_databases(db: Session, settings: Settings) -> list[DatabaseInfo]:
    databases = list_duckdb_databases(db)
    if settings.sql_lab_postgres_available:
        databases.append(
            DatabaseInfo(
                name=POSTGRES_DATABASE_NAME,
                label="Practice (PostgreSQL)",
                engine="postgres",
                description="A dedicated PostgreSQL database for relational SQL practice.",
                table_count=0,
            )
        )
    return databases


def _duckdb_table_sources(db: Session, dataset_slug: str) -> list[DuckDbTableSource]:
    stmt = (
        select(SqlTable)
        .join(Dataset, Dataset.id == SqlTable.dataset_id)
        .where(Dataset.slug == dataset_slug)
        .order_by(SqlTable.display_order)
    )
    tables = db.execute(stmt).scalars().all()
    if not tables:
        raise SqlEngineError(f"Database '{dataset_slug}' was not found.")
    return [
        DuckDbTableSource(
            table_name=t.table_name, file_path=str(resolve_repo_path(t.file_path)), file_format=t.file_format
        )
        for t in tables
    ]


def get_engine(db: Session, settings: Settings, engine_name: str, database_name: str) -> SqlEngine:
    if engine_name == "duckdb":
        return DuckDBEngine(database_name, _duckdb_table_sources(db, database_name))
    if engine_name == "postgres":
        if not settings.sql_lab_postgres_available:
            raise SqlEngineError("PostgreSQL is not configured for this installation.")
        return PostgresEngine(settings.sql_lab_postgres_url)  # type: ignore[arg-type]
    raise SqlEngineError(f"Unknown SQL engine '{engine_name}'.")
