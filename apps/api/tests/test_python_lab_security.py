"""Security tests for the Python Lab.

Two different verification strategies, matched to what's actually testable
in this environment (no Docker daemon available — see
docs/roadmap.md#what-phase-4-deliberately-does-not-build):

1. **Container isolation configuration** (network_mode=none, resource
   limits, read-only root FS, dropped capabilities, minimal/secret-free
   environment, single read-only dataset mount) — `DockerRuntimeBackend`
   never got to run against a real daemon, so these assert on the exact
   arguments it WOULD pass to `docker-py`'s `containers.run()`, via a mocked
   `docker` module. This is a genuine verification that the configuration is
   correct as written, not a live-behavior test.
2. **Execution-level limits** (timeout, output size, error isolation,
   concurrency ceiling) — verified for real, either directly against the
   real kernel (infrastructure/docker/python-sandbox/kernel.py) or through
   the full API stack via `InProcessKernelBackend` (see
   tests/python_lab_fakes.py).
"""

from __future__ import annotations

import signal
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.python_lab.docker_backend import DockerRuntimeBackend
from tests.python_lab_fakes import _kernel_module as kernel_module


@pytest.fixture
def mock_docker_module():
    """Patches the `docker` package as DockerRuntimeBackend would import it,
    so `.create()` can run to completion and we can inspect exactly what it
    told `containers.run()` to do."""
    mock_docker = MagicMock()
    mock_container = MagicMock()
    mock_container.id = "fake-container-id"
    mock_container.exec_run.return_value = (0, b'{"status": "pong"}\n')
    mock_docker.from_env.return_value.containers.run.return_value = mock_container
    mock_docker.errors.APIError = Exception
    mock_docker.errors.ImageNotFound = type("ImageNotFound", (Exception,), {})
    with patch.dict(sys.modules, {"docker": mock_docker}):
        yield mock_docker


class TestContainerIsolationConfiguration:
    def test_create_uses_network_mode_none(self, mock_docker_module, tmp_path) -> None:
        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        backend.create(dataset_mounts={}, timeout_seconds=10.0)
        _, kwargs = mock_docker_module.from_env.return_value.containers.run.call_args
        assert kwargs["network_mode"] == "none"

    def test_create_drops_all_capabilities_and_blocks_privilege_escalation(
        self, mock_docker_module, tmp_path
    ) -> None:
        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        backend.create(dataset_mounts={}, timeout_seconds=10.0)
        _, kwargs = mock_docker_module.from_env.return_value.containers.run.call_args
        assert kwargs["cap_drop"] == ["ALL"]
        assert "no-new-privileges" in kwargs["security_opt"]

    def test_create_uses_a_read_only_root_filesystem(self, mock_docker_module, tmp_path) -> None:
        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        backend.create(dataset_mounts={}, timeout_seconds=10.0)
        _, kwargs = mock_docker_module.from_env.return_value.containers.run.call_args
        assert kwargs["read_only"] is True
        assert "/tmp" in kwargs["tmpfs"]

    def test_create_enforces_memory_cpu_and_pid_limits_from_settings(
        self, mock_docker_module, tmp_path
    ) -> None:
        backend = DockerRuntimeBackend(
            datasets_dir=tmp_path, mem_limit="256m", nano_cpus=500_000_000, pids_limit=64
        )
        backend.create(dataset_mounts={}, timeout_seconds=10.0)
        _, kwargs = mock_docker_module.from_env.return_value.containers.run.call_args
        assert kwargs["mem_limit"] == "256m"
        assert kwargs["nano_cpus"] == 500_000_000
        assert kwargs["pids_limit"] == 64

    def test_create_runs_as_a_non_root_user(self, mock_docker_module, tmp_path) -> None:
        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        backend.create(dataset_mounts={}, timeout_seconds=10.0)
        _, kwargs = mock_docker_module.from_env.return_value.containers.run.call_args
        assert kwargs["user"] not in (None, "root", "0", 0)

    def test_create_mounts_exactly_one_volume_the_dataset_dir_read_only(
        self, mock_docker_module, tmp_path
    ) -> None:
        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        backend.create(dataset_mounts={}, timeout_seconds=10.0)
        _, kwargs = mock_docker_module.from_env.return_value.containers.run.call_args
        assert len(kwargs["volumes"]) == 1
        mount = kwargs["volumes"][str(tmp_path)]
        assert mount["mode"] == "ro"
        assert mount["bind"] == "/data"

    def test_create_never_passes_any_application_secret_into_the_container_environment(
        self, mock_docker_module, tmp_path
    ) -> None:
        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        backend.create(dataset_mounts={}, timeout_seconds=10.0)
        _, kwargs = mock_docker_module.from_env.return_value.containers.run.call_args
        env = kwargs["environment"]
        forbidden_substrings = [
            "DATABASE_URL",
            "POSTGRES",
            "SQL_LAB",
            "OPENAI",
            "KAGGLE",
            "SECRET",
            "PASSWORD",
        ]
        joined = " ".join(f"{k}={v}" for k, v in env.items()).upper()
        for forbidden in forbidden_substrings:
            assert forbidden not in joined, f"Sandbox container environment must never contain '{forbidden}'"

    def test_availability_reports_a_clear_reason_when_docker_is_unreachable(self, tmp_path) -> None:
        mock_docker = MagicMock()
        mock_docker.from_env.side_effect = RuntimeError("Cannot connect to the Docker daemon")
        with patch.dict(sys.modules, {"docker": mock_docker}):
            backend = DockerRuntimeBackend(datasets_dir=tmp_path)
            available, reason = backend.is_available()
        assert available is False
        assert "Docker" in reason


class TestDeadContainerRecovery:
    """Regression tests for a real bug: after a timeout kills the sandbox
    container (no restart_policy is set), both a subsequent execute() and
    restart() on that same runtime used to raise an unhandled
    docker.errors.APIError (HTTP 409, container not running) instead of the
    same clean, recoverable PythonRuntimeError every other failure path
    here produces — leaving service.py's runtime status falsely READY and
    surfacing a raw generic 500 to the user with no indication a new
    runtime was needed."""

    def test_execute_on_a_dead_container_raises_a_clean_runtime_error(
        self, mock_docker_module, tmp_path
    ) -> None:
        from app.python_lab.base import PythonRuntimeError

        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        handle = backend.create(dataset_mounts={}, timeout_seconds=10.0)

        container = mock_docker_module.from_env.return_value.containers.run.return_value
        container.exec_run.side_effect = Exception("409 Client Error: container is not running")
        # execute()/restart() look the runtime up via containers.get(handle),
        # not .run() (that's only called once, at create()) — point it at
        # the same mock container so the side_effect above actually applies.
        mock_docker_module.from_env.return_value.containers.get.return_value = container

        with pytest.raises(PythonRuntimeError, match="no longer running"):
            backend.execute(handle, "1 + 1", timeout_seconds=5.0)

    def test_restart_on_a_dead_container_raises_a_clean_runtime_error(
        self, mock_docker_module, tmp_path
    ) -> None:
        from app.python_lab.base import PythonRuntimeError

        backend = DockerRuntimeBackend(datasets_dir=tmp_path)
        handle = backend.create(dataset_mounts={}, timeout_seconds=10.0)

        container = mock_docker_module.from_env.return_value.containers.run.return_value
        container.exec_run.side_effect = Exception("409 Client Error: container is not running")
        mock_docker_module.from_env.return_value.containers.get.return_value = container

        with pytest.raises(PythonRuntimeError, match="no longer running"):
            backend.restart(handle)


class TestExecutionLevelLimits:
    @pytest.mark.skipif(
        not hasattr(signal, "SIGALRM"),
        reason="wall-clock interrupt is POSIX-only (production runs in Linux containers)",
    )
    def test_a_slow_computation_is_actually_interrupted_by_the_timeout(self) -> None:
        kernel = kernel_module.PythonKernel(timeout_seconds=0.5)
        result = kernel.execute("while True:\n    pass")
        assert result.status == "error"
        assert result.error.error_type == "TimeoutError"
        assert result.execution_time_ms < 3000

        # the kernel must still be usable after a timeout
        followup = kernel.execute("x = 1")
        assert followup.status == "success"

    def test_output_larger_than_the_limit_is_truncated_not_dropped_entirely(self) -> None:
        kernel = kernel_module.PythonKernel(timeout_seconds=5.0)
        result = kernel.execute("print('y' * 1_000_000)")
        assert result.stdout_truncated is True
        assert 0 < len(result.stdout) <= kernel_module.MAX_OUTPUT_CHARS


class TestConcurrencyLimit:
    def test_exceeding_the_concurrent_runtime_limit_is_rejected(self, client: TestClient) -> None:
        from app.dependencies.services import get_python_execution_service
        from app.main import app
        from app.python_lab.service import PythonExecutionService
        from tests.conftest import TestingSessionLocal
        from tests.python_lab_fakes import InProcessKernelBackend

        backend = InProcessKernelBackend()
        # The user's runtime count is NOT necessarily zero here — the DB is
        # shared/session-scoped across the whole test run, and other tests
        # create runtimes without always destroying them. Set the limit
        # relative to what's already active so this test is resilient to
        # test execution order.
        already_active = len(client.get("/api/v1/python/runtimes").json())
        low_limit_settings = Settings(python_lab_max_concurrent_runtimes=already_active + 2)

        def _low_limit_service() -> PythonExecutionService:
            return PythonExecutionService(TestingSessionLocal(), settings=low_limit_settings, backend=backend)

        # Swap in (and, after, restore — never simply pop, which would delete
        # the autouse fixture's own override key out from under its teardown)
        # the module-scoped override the `_override_python_lab_backend`
        # fixture already installed for this test.
        previous_override = app.dependency_overrides[get_python_execution_service]
        app.dependency_overrides[get_python_execution_service] = _low_limit_service
        try:
            first = client.post("/api/v1/python/runtimes")
            second = client.post("/api/v1/python/runtimes")
            third = client.post("/api/v1/python/runtimes")
            assert first.status_code == 201
            assert second.status_code == 201
            assert third.status_code == 400
        finally:
            app.dependency_overrides[get_python_execution_service] = previous_override


class TestErrorIsolationAcrossRuntimes:
    def test_two_runtimes_have_completely_independent_variable_namespaces(self, client: TestClient) -> None:
        runtime_a = client.post("/api/v1/python/runtimes").json()["id"]
        runtime_b = client.post("/api/v1/python/runtimes").json()["id"]

        client.post(f"/api/v1/python/runtimes/{runtime_a}/execute", json={"code": "secret = 'only in A'"})
        leak_check = client.post(f"/api/v1/python/runtimes/{runtime_b}/execute", json={"code": "secret"})

        assert leak_check.json()["status"] == "error"
        assert leak_check.json()["error"]["error_type"] == "NameError"
