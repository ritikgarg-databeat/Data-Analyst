"""Path/env resolution for the real, local dbt project at repo-root `dbt/`.

Mirrors app/sql/paths.py's REPO_ROOT convention. The dbt project itself reads
`DBT_DATA_DIR` (see dbt/models/staging/sources.yml's `external_location`) and
`DBT_WAREHOUSE_PATH` (see dbt/profiles/profiles.yml) via Jinja `env_var()` —
this module is the one place that resolves what those should be and hands
them to the `dbt` subprocess as environment variables.

Windows note: dbt-duckdb (a native Windows process here, not WSL/Git-Bash)
rejects MSYS-style POSIX paths ("/c/Users/..."). `Path.as_posix()` on Windows
keeps the drive letter but uses forward slashes ("C:/Users/...") — the one
format confirmed to work with dbt-duckdb's `external_location` templating.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from app.core.config import Settings
from app.sql.paths import REPO_ROOT

DBT_PROJECT_DIR = REPO_ROOT / "dbt"
DBT_PROFILES_DIR = DBT_PROJECT_DIR / "profiles"
DBT_TARGET_DIR = DBT_PROJECT_DIR / "target"

DEFAULT_DBT_DATA_DIR = REPO_ROOT / "data" / "sample" / "ecommerce"
DEFAULT_DBT_WAREHOUSE_PATH = REPO_ROOT / "data" / "warehouse" / "dev.duckdb"


def dbt_executable() -> Path:
    """The `dbt` console-script installed into this same venv, sitting next
    to the running interpreter (Scripts/ on Windows, bin/ elsewhere) — avoids
    depending on `dbt` being on PATH."""
    scripts_dir = Path(sys.executable).parent
    name = "dbt.exe" if sys.platform == "win32" else "dbt"
    return scripts_dir / name


def resolve_data_dir(settings: Settings) -> Path:
    return Path(settings.dbt_data_dir) if settings.dbt_data_dir else DEFAULT_DBT_DATA_DIR


def resolve_warehouse_path(settings: Settings) -> Path:
    return Path(settings.dbt_warehouse_path) if settings.dbt_warehouse_path else DEFAULT_DBT_WAREHOUSE_PATH


def build_dbt_env(settings: Settings) -> dict[str, str]:
    warehouse_path = resolve_warehouse_path(settings)
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["DBT_DATA_DIR"] = resolve_data_dir(settings).as_posix()
    env["DBT_WAREHOUSE_PATH"] = warehouse_path.as_posix()
    return env
