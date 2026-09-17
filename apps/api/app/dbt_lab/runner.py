"""Subprocess invocation of the real `dbt` CLI — no mocking, no simulated
output. One call in, one result out; DB persistence happens one layer up in
`app/dbt_lab/service.py`.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

from app.core.config import Settings
from app.dbt_lab.paths import DBT_PROFILES_DIR, DBT_PROJECT_DIR, build_dbt_env, dbt_executable


class DbtRunnerError(Exception):
    """The dbt executable itself couldn't be invoked (missing install, bad
    path, timeout) — distinct from a dbt command that runs to completion but
    reports failures/errors, which comes back as a normal DbtCliResult."""


@dataclass
class DbtCliResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_dbt(args: list[str], *, settings: Settings, timeout_seconds: float | None = None) -> DbtCliResult:
    """Runs `dbt <args> --project-dir dbt/ --profiles-dir dbt/profiles` for real."""
    executable = dbt_executable()
    if not executable.exists():
        raise DbtRunnerError(
            f"dbt executable not found at {executable}. Is dbt-core installed in this venv "
            "(`uv sync --extra dev` from apps/api)?"
        )

    full_args = [
        str(executable),
        "--no-use-colors",
        *args,
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROFILES_DIR),
    ]
    timeout = timeout_seconds if timeout_seconds is not None else settings.dbt_command_timeout_seconds

    started = time.monotonic()
    try:
        completed = subprocess.run(
            full_args,
            cwd=DBT_PROJECT_DIR,
            env=build_dbt_env(settings),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise DbtRunnerError(f"dbt command timed out after {timeout}s: {' '.join(args)}") from exc
    except OSError as exc:
        raise DbtRunnerError(f"Failed to launch dbt: {exc}") from exc

    return DbtCliResult(
        args=args,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.monotonic() - started,
    )
