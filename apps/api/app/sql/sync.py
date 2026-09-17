"""Syncs `database/seeds/sql_tables.yaml` into the `sql_tables` table.

row_count/column_count are computed from the actual source file via DuckDB
at sync time (not hand-maintained in the YAML) so they can never drift from
the real generated dataset.

Usage:
    uv run --project apps/api python -m app.sql.sync
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import yaml
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.sql_lab import SqlTable
from app.sql.paths import REPO_ROOT, resolve_repo_path

logger = logging.getLogger(__name__)

SEEDS_DIR = REPO_ROOT / "database" / "seeds"

_READ_FUNCTION_BY_FORMAT = {"csv": "read_csv_auto", "parquet": "read_parquet", "json": "read_json_auto"}


def _introspect(file_path: Path, file_format: str) -> tuple[int, int]:
    read_fn = _READ_FUNCTION_BY_FORMAT[file_format]
    con = duckdb.connect(":memory:")
    try:
        con.execute(f"CREATE VIEW t AS SELECT * FROM {read_fn}('{file_path.as_posix()}')")
        row_count = con.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        column_count = len(con.execute("DESCRIBE t").fetchall())
        return row_count, column_count
    finally:
        con.close()


def sync(db: Session) -> int:
    path = SEEDS_DIR / "sql_tables.yaml"
    rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []

    synced = 0
    for row in rows:
        dataset = db.query(Dataset).filter(Dataset.slug == row["dataset_slug"]).one_or_none()
        if dataset is None:
            logger.warning(
                "Skipping SQL table '%s': unknown dataset '%s'", row["table_name"], row["dataset_slug"]
            )
            continue

        file_path = resolve_repo_path(row["file_path"])
        row_count, column_count = _introspect(file_path, row["file_format"])

        table = (
            db.query(SqlTable)
            .filter(SqlTable.dataset_id == dataset.id, SqlTable.table_name == row["table_name"])
            .one_or_none()
        )
        if table is None:
            table = SqlTable(dataset_id=dataset.id, table_name=row["table_name"])
            db.add(table)
        table.dataset_id = dataset.id
        table.file_path = row["file_path"]
        table.file_format = row["file_format"]
        table.grain = row["grain"]
        table.display_order = row.get("display_order", 0)
        table.row_count = row_count
        table.column_count = column_count
        synced += 1

    # The session factory (app/core/database.py) uses autoflush=False, so on a
    # first-ever sync every SqlTable above is a newly `db.add()`-ed, not-yet-
    # flushed row — without this flush, the fresh `db.query(SqlTable)` below
    # would silently miss them all and leave every Dataset.row_count/
    # column_count at None forever (only a second sync run would "fix" it, by
    # which point the rows already exist from the first run).
    db.flush()

    # Keep the parent Dataset's own row/column counts roughly meaningful too —
    # sum across its tables (used only for display on the /datasets page).
    for dataset_slug in {r["dataset_slug"] for r in rows}:
        dataset = db.query(Dataset).filter(Dataset.slug == dataset_slug).one_or_none()
        if dataset is None:
            continue
        tables = db.query(SqlTable).filter(SqlTable.dataset_id == dataset.id).all()
        if tables:
            dataset.row_count = sum(t.row_count or 0 for t in tables)
            dataset.column_count = sum(t.column_count or 0 for t in tables)

    db.commit()
    logger.info("Synced %d SQL tables.", synced)
    return synced


if __name__ == "__main__":
    import logging as _logging

    from app.core.database import SessionLocal

    _logging.basicConfig(level=_logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
    session = SessionLocal()
    try:
        sync(session)
    finally:
        session.close()
