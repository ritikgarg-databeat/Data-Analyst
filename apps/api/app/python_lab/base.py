"""Runtime abstraction for the Python Lab — mirrors `app/sql/engines/base.py`'s
split between a plain-dataclass internal layer (this module) and the Pydantic
API layer (`app/schemas/python_lab.py`), for the same reason: the internal
layer is what a `PythonRuntimeBackend` actually returns, independent of how
it's later serialized to a client.

There is exactly one production backend, `DockerRuntimeBackend`
(app/python_lab/docker_backend.py) — it builds these dataclasses FROM the
JSON a sandbox container's kernel returns over `docker exec`, rather than
importing the sandbox's own dataclasses directly, so this app has zero
import-time coupling to `infrastructure/docker/python-sandbox/` (which the
`api` image never even contains — see the Dockerfile there and
docs/architecture.md#python-lab-phase-4)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PythonRuntimeError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class DataFrameColumn:
    name: str
    dtype: str
    null_count: int
    unique_count: int


@dataclass
class DataFrameSummary:
    row_count: int
    column_count: int
    columns: list[DataFrameColumn] = field(default_factory=list)
    preview_rows: list[list[Any]] = field(default_factory=list)
    preview_row_count: int = 0
    truncated: bool = False
    memory_usage_bytes: int | None = None


@dataclass
class PythonVariable:
    name: str
    type_name: str
    preview: str
    dataframe: DataFrameSummary | None = None
    shape: list[int] | None = None
    # The actual JSON-safe value (only populated for plain scalars/lists/dicts)
    # — what exercise grading compares; `preview` is display-only.
    value: Any = None


@dataclass
class ChartOutput:
    kind: str  # "matplotlib" | "plotly"
    format: str  # "png_base64" | "plotly_json"
    data: str
    title: str | None = None


@dataclass
class PythonError:
    error_type: str
    message: str
    line: int | None
    traceback_text: str
    hint: str | None = None


@dataclass
class PythonExecutionResult:
    status: str  # "success" | "error"
    stdout: str = ""
    stdout_truncated: bool = False
    display_value: PythonVariable | None = None
    variables: list[PythonVariable] = field(default_factory=list)
    charts: list[ChartOutput] = field(default_factory=list)
    error: PythonError | None = None
    execution_time_ms: int = 0

    @property
    def is_success(self) -> bool:
        return self.status == "success"


class PythonRuntimeBackend(ABC):
    """One live sandbox — created, executed against, restarted, and
    destroyed by a `PythonRuntimeManager` (service.py). A backend instance
    corresponds 1:1 to a `PythonRuntime` DB row's `container_id`."""

    @abstractmethod
    def create(self, *, dataset_mounts: dict[str, str], timeout_seconds: float) -> str:
        """Starts the sandbox; returns an opaque backend-specific handle
        (e.g. a Docker container id) to persist on the PythonRuntime row."""

    @abstractmethod
    def execute(self, handle: str, code: str, *, timeout_seconds: float) -> PythonExecutionResult: ...

    @abstractmethod
    def restart(self, handle: str) -> None:
        """Clears the runtime's variable namespace in place — the handle
        stays valid (mirrors the Definition of Done's 'Runtime Reset':
        destroy current runtime, clear variables, recreate sandbox,
        preserve saved code — the *code* lives in the DB, not the sandbox,
        so nothing else needs to change)."""

    @abstractmethod
    def destroy(self, handle: str) -> None: ...

    @abstractmethod
    def is_available(self) -> tuple[bool, str | None]:
        """(available, reason_if_not) — never raises; mirrors how the SQL
        Lab reports the Postgres engine unavailable instead of crashing."""
