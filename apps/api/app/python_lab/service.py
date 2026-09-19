"""Runtime lifecycle + execution orchestration — the DB-aware layer between
the routers and `DockerRuntimeBackend`. Mirrors `app/sql/service.py`'s shape:
one service class routers/exercise-service depend on via DI, engine/backend
resolution isolated behind it, execution optionally logged to history.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError, NotFoundError
from app.models.dataset import Dataset
from app.models.enums import PythonRuntimeStatus
from app.models.python_lab import PythonExecution, PythonRuntime
from app.models.sql_lab import SqlTable
from app.python_lab.base import PythonExecutionResult, PythonRuntimeBackend, PythonRuntimeError
from app.python_lab.docker_backend import DockerRuntimeBackend
from app.sql.paths import REPO_ROOT

DEFAULT_DATASETS_DIR = REPO_ROOT / "data" / "sample"
DEFAULT_IMPORTED_DATASETS_DIR = REPO_ROOT / "data" / "datasets"  # Phase 5 user-imported datasets


@dataclass
class PythonDatasetFile:
    dataset_slug: str
    dataset_name: str
    label: str  # e.g. "orders.csv" or "orders_sample.csv"
    container_path: str  # e.g. "/data/ecommerce/orders.csv"
    file_format: str
    grain: str | None
    row_count: int | None
    column_count: int | None
    suggested_code: str


class PythonExecutionService:
    def __init__(
        self,
        db: Session,
        settings: Settings | None = None,
        backend: PythonRuntimeBackend | None = None,
        user_id: str | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.user_id = user_id
        configured_imports = (
            Path(self.settings.python_lab_host_datasets_dir)
            if self.settings.python_lab_host_datasets_dir
            else DEFAULT_IMPORTED_DATASETS_DIR
        )
        private_imports = (
            configured_imports.parent / "users" / user_id / "datasets" if user_id else configured_imports
        )
        self.backend = backend or DockerRuntimeBackend(
            # See Settings.python_lab_host_data_dir's docstring: the Docker
            # daemon always resolves a volume-mount spec against the HOST
            # filesystem, so under Docker Compose this must be the host-side
            # path, not this process's own (possibly containerized) view of it.
            datasets_dir=Path(self.settings.python_lab_host_data_dir)
            if self.settings.python_lab_host_data_dir
            else DEFAULT_DATASETS_DIR,
            extra_datasets_dir=private_imports,
            mem_limit=self.settings.python_lab_mem_limit,
            nano_cpus=self.settings.python_lab_nano_cpus,
            pids_limit=self.settings.python_lab_pids_limit,
        )

    def is_available(self) -> tuple[bool, str | None]:
        return self.backend.is_available()

    # --- Runtime lifecycle -------------------------------------------------

    def create_runtime(
        self, user_id: str, *, workspace_id: str | None = None, count_toward_limit: bool = True
    ) -> PythonRuntime:
        available, reason = self.is_available()
        if not available:
            raise AppError(f"The Python Lab sandbox is not available: {reason}")

        if count_toward_limit:
            active_count = (
                self.db.execute(
                    select(PythonRuntime).where(
                        PythonRuntime.user_id == user_id,
                        PythonRuntime.status.in_(
                            [
                                PythonRuntimeStatus.STARTING,
                                PythonRuntimeStatus.READY,
                                PythonRuntimeStatus.BUSY,
                            ]
                        ),
                    )
                )
                .scalars()
                .all()
            )
            if len(active_count) >= self.settings.python_lab_max_concurrent_runtimes:
                raise AppError(
                    f"You already have {len(active_count)} active Python runtimes "
                    f"(the limit is {self.settings.python_lab_max_concurrent_runtimes}). "
                    "Restart or close one before starting another."
                )

        runtime = PythonRuntime(
            user_id=user_id,
            workspace_id=workspace_id,
            status=PythonRuntimeStatus.STARTING,
            timeout_seconds=int(self.settings.python_lab_execution_timeout_seconds),
        )
        self.db.add(runtime)
        self.db.commit()
        self.db.refresh(runtime)

        try:
            handle = self.backend.create(
                dataset_mounts={}, timeout_seconds=self.settings.python_lab_execution_timeout_seconds
            )
        except PythonRuntimeError as exc:
            runtime.status = PythonRuntimeStatus.ERROR
            runtime.error_message = str(exc)
            self.db.commit()
            raise AppError(f"Failed to start the Python sandbox: {exc}") from exc
        except Exception as exc:
            # A failure mode `DockerRuntimeBackend.create` doesn't already
            # wrap as PythonRuntimeError (e.g. a connection-level exception
            # from the Docker daemon) used to propagate uncaught, leaving
            # this row permanently stuck at STARTING — counting forever
            # toward python_lab_max_concurrent_runtimes above, and (if a
            # container actually started before the failure) leaking it,
            # since nothing held its id to destroy it.
            runtime.status = PythonRuntimeStatus.ERROR
            runtime.error_message = str(exc)
            self.db.commit()
            raise AppError(f"Failed to start the Python sandbox: {exc}") from exc

        runtime.container_id = handle
        runtime.status = PythonRuntimeStatus.READY
        self.db.commit()
        self.db.refresh(runtime)
        return runtime

    def get_runtime(self, runtime_id: str, user_id: str) -> PythonRuntime:
        runtime = self.db.get(PythonRuntime, runtime_id)
        if runtime is None or runtime.user_id != user_id:
            raise NotFoundError(f"Python runtime '{runtime_id}' was not found.")
        return runtime

    def list_runtimes(self, user_id: str) -> list[PythonRuntime]:
        stmt = (
            select(PythonRuntime)
            .where(PythonRuntime.user_id == user_id, PythonRuntime.status != PythonRuntimeStatus.STOPPED)
            .order_by(PythonRuntime.last_used_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def execute(
        self,
        runtime_id: str,
        user_id: str,
        code: str,
        *,
        workspace_id: str | None = None,
        log_history: bool = True,
    ) -> PythonExecutionResult:
        runtime = self.get_runtime(runtime_id, user_id)
        if (
            runtime.status not in (PythonRuntimeStatus.READY, PythonRuntimeStatus.BUSY)
            or not runtime.container_id
        ):
            raise AppError("This runtime isn't ready to run code — create a new one.")

        runtime.status = PythonRuntimeStatus.BUSY
        self.db.commit()
        try:
            result = self.backend.execute(
                runtime.container_id, code, timeout_seconds=float(runtime.timeout_seconds)
            )
        except PythonRuntimeError as exc:
            runtime.status = PythonRuntimeStatus.ERROR
            runtime.error_message = str(exc)
            self.db.commit()
            raise AppError(f"The Python sandbox failed: {exc}") from exc
        finally:
            if runtime.status == PythonRuntimeStatus.BUSY:
                runtime.status = PythonRuntimeStatus.READY
            runtime.last_used_at = datetime.now(UTC)
            self.db.commit()

        if log_history:
            self.db.add(
                PythonExecution(
                    user_id=user_id,
                    workspace_id=workspace_id,
                    code=code,
                    status=result.status,
                    stdout=result.stdout or None,
                    error_message=result.error.message if result.error else None,
                    execution_time_ms=result.execution_time_ms,
                )
            )
            self.db.commit()

        return result

    def restart_runtime(self, runtime_id: str, user_id: str) -> PythonRuntime:
        runtime = self.get_runtime(runtime_id, user_id)
        if not runtime.container_id:
            raise AppError("This runtime was never started.")
        try:
            self.backend.restart(runtime.container_id)
        except PythonRuntimeError as exc:
            runtime.status = PythonRuntimeStatus.ERROR
            runtime.error_message = str(exc)
            self.db.commit()
            raise AppError(f"Failed to restart the Python sandbox: {exc}") from exc
        runtime.status = PythonRuntimeStatus.READY
        runtime.error_message = None
        runtime.last_used_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(runtime)
        return runtime

    def destroy_runtime(self, runtime_id: str, user_id: str) -> None:
        runtime = self.get_runtime(runtime_id, user_id)
        if runtime.container_id:
            self.backend.destroy(runtime.container_id)
        runtime.status = PythonRuntimeStatus.STOPPED
        self.db.commit()

    def reap_idle_runtimes(self) -> int:
        """Destroys runtimes untouched for longer than the configured TTL —
        called on API startup and opportunistically from list/create (see
        app/main.py's lifespan and the router). Never raises: a single
        unreachable container shouldn't block the sweep of the rest."""
        cutoff = datetime.now(UTC) - timedelta(seconds=self.settings.python_lab_runtime_idle_ttl_seconds)
        stmt = select(PythonRuntime).where(
            PythonRuntime.status.in_(
                [PythonRuntimeStatus.READY, PythonRuntimeStatus.BUSY, PythonRuntimeStatus.ERROR]
            ),
            PythonRuntime.last_used_at < cutoff,
        )
        stale = list(self.db.execute(stmt).scalars().all())

        # A STARTING row whose creation never reached either the READY or
        # ERROR transition (e.g. the process was killed mid-request, before
        # create_runtime's own except-and-mark-ERROR handling could run) was
        # never included in the query above and so would count against
        # python_lab_max_concurrent_runtimes forever, with no code path left
        # to recover it. `created_at` (not `last_used_at`, which a STARTING
        # row never gets to set) against a short, fixed grace period —
        # creation normally takes low single-digit seconds — is what lets
        # this be safely swept without racing a request that's still
        # genuinely in the middle of `create_runtime` right now.
        stuck_cutoff = datetime.now(UTC) - timedelta(seconds=120)
        stuck_stmt = select(PythonRuntime).where(
            PythonRuntime.status == PythonRuntimeStatus.STARTING,
            PythonRuntime.created_at < stuck_cutoff,
        )
        stuck = list(self.db.execute(stuck_stmt).scalars().all())

        for runtime in [*stale, *stuck]:
            if runtime.container_id:
                with contextlib.suppress(Exception):  # best-effort cleanup
                    self.backend.destroy(runtime.container_id)
            runtime.status = PythonRuntimeStatus.STOPPED
        self.db.commit()
        return len(stale) + len(stuck)

    # --- History -------------------------------------------------------

    def list_history(
        self, user_id: str, *, workspace_id: str | None = None, limit: int = 50
    ) -> list[PythonExecution]:
        stmt = select(PythonExecution).where(PythonExecution.user_id == user_id)
        if workspace_id:
            stmt = stmt.where(PythonExecution.workspace_id == workspace_id)
        stmt = stmt.order_by(PythonExecution.executed_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def delete_history_entry(self, user_id: str, history_id: str) -> None:
        entry = self.db.get(PythonExecution, history_id)
        if entry is None or entry.user_id != user_id:
            raise NotFoundError(f"History entry '{history_id}' was not found.")
        self.db.delete(entry)
        self.db.commit()

    # --- Datasets --------------------------------------------------------

    def list_datasets(self, user_id: str | None = None) -> list[PythonDatasetFile]:
        """Every dataset file a Python Lab session can `pd.read_csv(...)` /
        `pd.read_parquet(...)` off the read-only /data mount — reuses
        `Dataset` (Phase 1/2) and, where present, `SqlTable` (Phase 3)
        rather than introducing a new dataset-file model. `_container_path_for`
        covers both of `DockerRuntimeBackend`'s read-only mounts: the
        Phase 1-3 curriculum data under data/sample/ (-> /data/...) and
        Phase 5 user-imported datasets under data/datasets/ (-> /data/datasets/...)."""
        effective_user_id = user_id or self.user_id
        files: list[PythonDatasetFile] = []
        datasets = (
            self.db.execute(
                select(Dataset).where(
                    or_(Dataset.owner_user_id.is_(None), Dataset.owner_user_id == effective_user_id)
                )
            )
            .scalars()
            .all()
        )
        for dataset in datasets:
            table_stmt = (
                select(SqlTable).where(SqlTable.dataset_id == dataset.id).order_by(SqlTable.display_order)
            )
            tables = list(self.db.execute(table_stmt).scalars().all())
            if tables:
                for table in tables:
                    container_path = _container_path_for(table.file_path)
                    if container_path is None:
                        continue
                    files.append(
                        PythonDatasetFile(
                            dataset_slug=dataset.slug,
                            dataset_name=dataset.name,
                            label=f"{table.table_name}.{table.file_format}",
                            container_path=container_path,
                            file_format=table.file_format,
                            grain=table.grain,
                            row_count=table.row_count,
                            column_count=table.column_count,
                            suggested_code=_suggested_load_code(
                                table.table_name, container_path, table.file_format
                            ),
                        )
                    )
            elif dataset.file_path and dataset.file_format:
                container_path = _container_path_for(dataset.file_path)
                if container_path is None:
                    continue
                relative = container_path.removeprefix("/data/")
                var_name = dataset.slug.replace("-", "_")
                files.append(
                    PythonDatasetFile(
                        dataset_slug=dataset.slug,
                        dataset_name=dataset.name,
                        label=relative,
                        container_path=container_path,
                        file_format=dataset.file_format,
                        grain=None,
                        row_count=dataset.row_count,
                        column_count=dataset.column_count,
                        suggested_code=_suggested_load_code(var_name, container_path, dataset.file_format),
                    )
                )
        return files


def _container_path_for(file_path: str) -> str | None:
    """Maps a repo-relative dataset file path to its path inside the Python
    Lab sandbox container — see `DockerRuntimeBackend.create()`'s two
    read-only mounts (data/sample -> /data, data/datasets -> /data/datasets).
    Returns None for a path under neither (nothing to mount it from)."""
    if "data/sample/" in file_path:
        return f"/data/{file_path.split('data/sample/', 1)[-1]}"
    if "data/datasets/" in file_path:
        return f"/data/datasets/{file_path.split('data/datasets/', 1)[-1]}"
    normalized = file_path.replace("\\", "/")
    if "/datasets/" in normalized and normalized.startswith("data/users/"):
        return f"/data/datasets/{normalized.split('/datasets/', 1)[-1]}"
    return None


_READ_FUNCTION_BY_FORMAT = {"csv": "read_csv", "parquet": "read_parquet", "json": "read_json"}


def _suggested_load_code(var_name: str, container_path: str, file_format: str) -> str:
    read_fn = _READ_FUNCTION_BY_FORMAT.get(file_format, "read_csv")
    return f'{var_name} = pd.{read_fn}("{container_path}")'
