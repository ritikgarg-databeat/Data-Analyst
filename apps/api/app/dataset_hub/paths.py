"""Canonical on-disk layout for Dataset Hub data (section 41 of the Phase 5
spec) — actual data files never live in PostgreSQL, only their repo-relative
paths do (on `DatasetTable.file_path` / `SqlTable.file_path`).

    data/
        raw/<dataset-slug>/<original-filename>   - untouched upload/download, kept for
                                                     audit + re-processing
        processed/<dataset-slug>/                - scratch space during import (e.g. an
                                                     XLSX sheet exported to CSV before DuckDB
                                                     converts it) — safe to delete, never queried
        datasets/<dataset-slug>/<table>.parquet   - canonical Parquet each table is queried
                                                     from (DuckDB/SQL Lab/Python Lab all read
                                                     this, never `raw/`)

`data/sample/` (Phase 1-3's built-in curriculum datasets) is untouched and
deliberately separate — nothing here ever writes to it.
"""

from __future__ import annotations

from pathlib import Path

from app.sql.paths import REPO_ROOT

DATA_ROOT = REPO_ROOT / "data"
RAW_DIR = DATA_ROOT / "raw"
PROCESSED_DIR = DATA_ROOT / "processed"
DATASETS_DIR = DATA_ROOT / "datasets"


def raw_dir_for(slug: str) -> Path:
    path = RAW_DIR / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_dir_for(slug: str) -> Path:
    path = PROCESSED_DIR / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def datasets_dir_for(slug: str) -> Path:
    path = DATASETS_DIR / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()
