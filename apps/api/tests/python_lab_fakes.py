"""A test-only `PythonRuntimeBackend` that runs the REAL sandbox kernel
in-process (no Docker) — see infrastructure/docker/python-sandbox/kernel.py.

This is not a mock: `execute()` genuinely runs the submitted code through
`PythonKernel`, with real pandas/numpy/etc (installed via apps/api's
`sandbox` extra). What it does NOT verify is the container boundary itself
(network isolation, resource limits, the docker-py orchestration in
app/python_lab/docker_backend.py) — that's covered separately by
test_python_lab_security.py's design-review-level tests and
DockerRuntimeBackend's own mock-based unit tests, mirroring exactly how
Phase 3 could exercise the DuckDB engine for real but only mock-test the
Postgres engine (no live instance available in this environment either).
"""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path

from app.python_lab.base import (
    ChartOutput,
    DataFrameColumn,
    DataFrameSummary,
    PythonError,
    PythonExecutionResult,
    PythonRuntimeBackend,
    PythonRuntimeError,
    PythonVariable,
)
from app.python_lab.service import DEFAULT_DATASETS_DIR

# The real DockerRuntimeBackend bind-mounts DEFAULT_DATASETS_DIR to `/data`
# inside the container; this fake has no container, so it simulates the
# same mount with a literal path rewrite before handing code to the kernel.
_DATA_MOUNT_PREFIX = "/data/"
_REAL_DATA_PREFIX = DEFAULT_DATASETS_DIR.as_posix() + "/"

KERNEL_PATH = (
    Path(__file__).resolve().parents[3] / "infrastructure" / "docker" / "python-sandbox" / "kernel.py"
)
_spec = importlib.util.spec_from_file_location("sandbox_kernel", KERNEL_PATH)
_kernel_module = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("sandbox_kernel", _kernel_module)
_spec.loader.exec_module(_kernel_module)

PythonKernel = _kernel_module.PythonKernel


def _convert_dataframe(raw) -> DataFrameSummary | None:
    if raw is None:
        return None
    return DataFrameSummary(
        row_count=raw.row_count,
        column_count=raw.column_count,
        columns=[
            DataFrameColumn(
                name=c["name"], dtype=c["dtype"], null_count=c["null_count"], unique_count=c["unique_count"]
            )
            for c in raw.columns
        ],
        preview_rows=raw.preview_rows,
        preview_row_count=raw.preview_row_count,
        truncated=raw.truncated,
        memory_usage_bytes=raw.memory_usage_bytes,
    )


def _convert_variable(raw) -> PythonVariable | None:
    if raw is None:
        return None
    return PythonVariable(
        name=raw.name,
        type_name=raw.type_name,
        preview=raw.preview,
        dataframe=_convert_dataframe(raw.dataframe),
        shape=raw.shape,
        value=raw.value,
    )


def _convert_error(raw) -> PythonError | None:
    if raw is None:
        return None
    return PythonError(
        error_type=raw.error_type,
        message=raw.message,
        line=raw.line,
        traceback_text=raw.traceback_text,
        hint=raw.hint,
    )


def _convert_result(raw) -> PythonExecutionResult:
    return PythonExecutionResult(
        status=raw.status,
        stdout=raw.stdout,
        stdout_truncated=raw.stdout_truncated,
        display_value=_convert_variable(raw.display_value),
        variables=[_convert_variable(v) for v in raw.variables],
        charts=[ChartOutput(kind=c.kind, format=c.format, data=c.data, title=c.title) for c in raw.charts],
        error=_convert_error(raw.error),
        execution_time_ms=raw.execution_time_ms,
    )


class InProcessKernelBackend(PythonRuntimeBackend):
    """Real execution, fake isolation — see module docstring."""

    def __init__(self, *, available: bool = True, unavailable_reason: str | None = None) -> None:
        self.kernels: dict[str, PythonKernel] = {}
        self._available = available
        self._unavailable_reason = unavailable_reason or "Docker is not reachable (simulated for tests)."
        self.destroyed_handles: list[str] = []

    def is_available(self) -> tuple[bool, str | None]:
        return self._available, None if self._available else self._unavailable_reason

    def create(self, *, dataset_mounts: dict[str, str], timeout_seconds: float) -> str:
        if not self._available:
            raise PythonRuntimeError(self._unavailable_reason)
        handle = str(uuid.uuid4())
        self.kernels[handle] = PythonKernel(timeout_seconds=timeout_seconds)
        return handle

    def execute(self, handle: str, code: str, *, timeout_seconds: float) -> PythonExecutionResult:
        kernel = self.kernels.get(handle)
        if kernel is None:
            raise PythonRuntimeError(f"No such runtime: {handle}")
        code = code.replace(_DATA_MOUNT_PREFIX, _REAL_DATA_PREFIX)
        return _convert_result(kernel.execute(code))

    def restart(self, handle: str) -> None:
        kernel = self.kernels.get(handle)
        if kernel is None:
            raise PythonRuntimeError(f"No such runtime: {handle}")
        kernel.restart()

    def destroy(self, handle: str) -> None:
        self.kernels.pop(handle, None)
        self.destroyed_handles.append(handle)
