"""The one production `PythonRuntimeBackend` — every execution of
user-submitted Python happens in a container of the
`infrastructure/docker/python-sandbox` image, never in this process.

Isolation posture (see docs/architecture.md#python-lab-phase-4 for the full
writeup and rationale):
  - `network_mode="none"`         — no network stack at all, not even loopback
                                     out of the container; nothing to attack
  - `mem_limit` / `nano_cpus`     — hard resource ceilings (Settings-configurable)
  - `pids_limit`                  — caps fork-bombs
  - `read_only=True` root FS      — only `/tmp` (tmpfs, size-capped) is writable
  - non-root user (uid 1000)      — baked into the image, not set here
  - `cap_drop=["ALL"]`, `security_opt=["no-new-privileges"]`
  - dataset directory mounted `ro`— the sandbox can read practice datasets,
                                     never write them, never see anything else
                                     on the host filesystem
  - no volume/env exposes `DATABASE_URL`, `SQL_LAB_POSTGRES_URL`, or any other
    app secret — the container's environment is built from scratch here, never
    inherited from the API process's own environment

Because `network_mode="none"` removes the container's network stack
entirely, published ports don't work — communication instead goes through
`docker exec`, which rides the Docker daemon's own control channel (not
container networking), running `client.py` *inside* the container to talk to
`server.py`'s Unix socket over local filesystem IPC. This is what makes true
"no network access" isolation compatible with still being able to run code
in a persistent, stateful kernel.
"""

from __future__ import annotations

import base64
import contextlib
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
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

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = "data-analyst-lab-python-sandbox:latest"
CONTAINER_DATA_MOUNT = "/data"


class DockerRuntimeBackend(PythonRuntimeBackend):
    def __init__(
        self,
        *,
        datasets_dir: Path,
        extra_datasets_dir: Path | None = None,
        image: str = SANDBOX_IMAGE,
        mem_limit: str = "512m",
        nano_cpus: int = 1_000_000_000,  # 1 CPU
        pids_limit: int = 128,
    ) -> None:
        self.datasets_dir = datasets_dir
        # Phase 5: user-imported datasets (data/datasets/), mounted read-only
        # alongside `datasets_dir` (data/sample/) at /data/datasets — see
        # app/python_lab/service.py's `_container_path_for`. Optional and
        # silently skipped if the directory doesn't exist yet (e.g. before
        # any dataset has ever been imported) rather than failing container
        # creation over a directory nothing currently needs.
        self.extra_datasets_dir = extra_datasets_dir
        self.image = image
        self.mem_limit = mem_limit
        self.nano_cpus = nano_cpus
        self.pids_limit = pids_limit
        self._client = None

    def _get_client(self):
        if self._client is None:
            import docker

            self._client = docker.from_env()
        return self._client

    def is_available(self) -> tuple[bool, str | None]:
        # Catches a misresolved PYTHON_LAB_HOST_DATA_DIR early (e.g. a Compose
        # variable-interpolation edge case leaving a literal, nonexistent
        # path) with a clear message, instead of a confusing failure deep
        # inside container creation.
        if not self.datasets_dir.is_dir():
            return False, (
                f"The configured dataset directory does not exist: '{self.datasets_dir}'. "
                "Check PYTHON_LAB_HOST_DATA_DIR in your .env."
            )
        try:
            import docker
        except ImportError:
            return False, "The 'docker' package is not installed."
        try:
            client = self._get_client()
            client.ping()
        except Exception as exc:  # noqa: BLE001 — any Docker-unreachable reason maps to "unavailable"
            return False, f"Docker is not reachable ({type(exc).__name__}): {exc}"
        try:
            client.images.get(self.image)
        except docker.errors.ImageNotFound:
            return False, (
                f"The sandbox image '{self.image}' has not been built yet. "
                "Run: docker compose build python-sandbox"
            )
        except Exception as exc:  # noqa: BLE001
            return False, f"Could not check for the sandbox image ({type(exc).__name__}): {exc}"
        return True, None

    def create(self, *, dataset_mounts: dict[str, str], timeout_seconds: float) -> str:
        import docker

        client = self._get_client()
        name = f"pylab-{uuid.uuid4().hex[:12]}"
        volumes = {str(self.datasets_dir): {"bind": CONTAINER_DATA_MOUNT, "mode": "ro"}}
        if self.extra_datasets_dir and self.extra_datasets_dir.is_dir():
            volumes[str(self.extra_datasets_dir)] = {"bind": f"{CONTAINER_DATA_MOUNT}/datasets", "mode": "ro"}
        try:
            container = client.containers.run(
                self.image,
                detach=True,
                name=name,
                network_mode="none",
                mem_limit=self.mem_limit,
                nano_cpus=self.nano_cpus,
                pids_limit=self.pids_limit,
                read_only=True,
                tmpfs={"/tmp": "size=256m,mode=1777"},
                volumes=volumes,
                user="1000:1000",
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                environment={"SANDBOX_TIMEOUT_SECONDS": str(timeout_seconds)},
            )
        except docker.errors.APIError as exc:
            raise PythonRuntimeError(f"Failed to start the Python sandbox: {exc}") from exc

        if not self._wait_until_ready(container, timeout_seconds=10.0):
            with contextlib.suppress(Exception):
                container.kill()
                container.remove(force=True)
            raise PythonRuntimeError("The Python sandbox did not become ready in time.")
        return container.id

    def _wait_until_ready(self, container, *, timeout_seconds: float) -> bool:
        import time

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                exit_code, _ = container.exec_run(["python", "/sandbox/client.py", "ping"])
                if exit_code == 0:
                    return True
            except Exception:  # noqa: S110, BLE001 — container may still be starting
                pass
            time.sleep(0.2)
        return False

    def execute(self, handle: str, code: str, *, timeout_seconds: float) -> PythonExecutionResult:
        import docker

        client = self._get_client()
        try:
            container = client.containers.get(handle)
        except Exception as exc:  # noqa: BLE001
            raise PythonRuntimeError(f"Sandbox runtime is no longer available: {exc}") from exc

        encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")

        def _run() -> tuple[int, bytes]:
            return container.exec_run(["python", "/sandbox/client.py", "execute", encoded])

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run)
            try:
                exit_code, output = future.result(timeout=timeout_seconds + 8.0)
            except FutureTimeoutError as exc:
                with contextlib.suppress(Exception):
                    container.kill()
                # `container.kill()` permanently stops the container (no
                # restart_policy is set at create()). Raising here — instead
                # of returning a normal error result — is what makes
                # service.py's execute() mark the runtime ERROR instead of
                # falling through to its `finally` block, which otherwise
                # unconditionally reset status back to READY even though the
                # container backing it is now dead, so every subsequent call
                # (execute or restart) crashed with an unhandled
                # docker.errors.APIError (409, container not running).
                raise PythonRuntimeError(
                    f"Execution exceeded the {timeout_seconds:.0f}s time limit and the sandbox was reset. "
                    "Start a new runtime to continue."
                ) from exc
            except docker.errors.APIError as exc:
                # The container died between calls (e.g. a previous timeout's
                # kill(), or the daemon reaping it) — surface this as the same
                # recoverable "runtime is dead" signal, not a raw 500.
                raise PythonRuntimeError(f"Sandbox runtime is no longer running: {exc}") from exc

        return self._parse_exec_output(output)

    def _parse_exec_output(self, output: bytes) -> PythonExecutionResult:
        try:
            payload = json.loads(output.decode("utf-8").strip().splitlines()[-1])
        except (ValueError, IndexError) as exc:
            return PythonExecutionResult(
                status="error",
                error=PythonError(
                    error_type="SandboxProtocolError",
                    message=f"The sandbox returned an unreadable response: {exc}",
                    line=None,
                    traceback_text=output.decode("utf-8", errors="replace")[:2000],
                ),
            )

        status = payload.get("status")
        if status in ("client_error", "server_error"):
            return PythonExecutionResult(
                status="error",
                error=PythonError(
                    error_type="SandboxError",
                    message=payload.get("message", "Unknown sandbox error"),
                    line=None,
                    traceback_text="",
                ),
            )
        if status != "ok":
            return PythonExecutionResult(
                status="error",
                error=PythonError(
                    error_type="SandboxProtocolError",
                    message=f"Unexpected sandbox status: {status!r}",
                    line=None,
                    traceback_text="",
                ),
            )

        result = payload["result"]
        return PythonExecutionResult(
            status=result["status"],
            stdout=result.get("stdout", ""),
            stdout_truncated=result.get("stdout_truncated", False),
            display_value=_variable_from_dict(result.get("display_value")),
            variables=[_variable_from_dict(v) for v in result.get("variables", [])],
            charts=[
                ChartOutput(kind=c["kind"], format=c["format"], data=c["data"], title=c.get("title"))
                for c in result.get("charts", [])
            ],
            error=_error_from_dict(result.get("error")),
            execution_time_ms=result.get("execution_time_ms", 0),
        )

    def restart(self, handle: str) -> None:
        import docker

        client = self._get_client()
        try:
            container = client.containers.get(handle)
            exit_code, output = container.exec_run(["python", "/sandbox/client.py", "restart"])
        except docker.errors.APIError as exc:
            # The container is no longer running (e.g. killed by a previous
            # execute() timeout) — a real, previously-unhandled case where
            # this raised all the way to a generic 500 instead of the clean
            # "start a new runtime" signal every other failure path here
            # produces.
            raise PythonRuntimeError(f"Sandbox runtime is no longer running: {exc}") from exc
        if exit_code != 0:
            raise PythonRuntimeError(f"Failed to restart the sandbox runtime: {output!r}")

    def destroy(self, handle: str) -> None:
        client = self._get_client()
        try:
            container = client.containers.get(handle)
        except Exception:  # noqa: BLE001 — already gone is fine
            return
        with contextlib.suppress(Exception):
            container.kill()
        with contextlib.suppress(Exception):
            container.remove(force=True)


def _variable_from_dict(data: dict | None) -> PythonVariable | None:
    if data is None:
        return None
    dataframe = None
    if data.get("dataframe"):
        df = data["dataframe"]
        dataframe = DataFrameSummary(
            row_count=df["row_count"],
            column_count=df["column_count"],
            columns=[DataFrameColumn(**c) for c in df.get("columns", [])],
            preview_rows=df.get("preview_rows", []),
            preview_row_count=df.get("preview_row_count", 0),
            truncated=df.get("truncated", False),
            memory_usage_bytes=df.get("memory_usage_bytes"),
        )
    return PythonVariable(
        name=data["name"],
        type_name=data["type_name"],
        preview=data["preview"],
        dataframe=dataframe,
        shape=data.get("shape"),
        value=data.get("value"),
    )


def _error_from_dict(data: dict | None) -> PythonError | None:
    if data is None:
        return None
    return PythonError(
        error_type=data["error_type"],
        message=data["message"],
        line=data.get("line"),
        traceback_text=data.get("traceback_text", ""),
        hint=data.get("hint"),
    )
