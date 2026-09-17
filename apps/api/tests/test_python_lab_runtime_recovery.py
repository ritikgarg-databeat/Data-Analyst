"""Regression tests: a runtime whose creation fails must never get stuck at
STARTING forever (it should transition to ERROR so it stops counting toward
python_lab_max_concurrent_runtimes and can be swept), and reap_idle_runtimes
must sweep a STARTING row that never got the chance to reach either READY
or ERROR (e.g. the process died mid-request)."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import PythonRuntimeStatus
from app.models.python_lab import PythonRuntime
from app.python_lab.base import PythonExecutionResult, PythonRuntimeBackend, PythonRuntimeError
from app.python_lab.service import PythonExecutionService

_TEST_SETTINGS = Settings(python_lab_max_concurrent_runtimes=4, python_lab_runtime_idle_ttl_seconds=3600)


class _AlwaysAvailableBackend(PythonRuntimeBackend):
    def is_available(self) -> tuple[bool, str | None]:
        return True, None

    def create(self, *, dataset_mounts: dict[str, str], timeout_seconds: float) -> str:
        raise NotImplementedError

    def execute(self, handle: str, code: str, *, timeout_seconds: float) -> PythonExecutionResult:
        raise NotImplementedError

    def restart(self, handle: str) -> None:
        raise NotImplementedError

    def destroy(self, handle: str) -> None:
        pass


class _RaisesGenericExceptionOnCreate(_AlwaysAvailableBackend):
    def create(self, *, dataset_mounts: dict[str, str], timeout_seconds: float) -> str:
        # Deliberately NOT a PythonRuntimeError -- simulates a failure mode
        # the backend doesn't already translate (e.g. a raw connection-level
        # exception from the Docker daemon).
        raise RuntimeError("the daemon connection reset unexpectedly")


class _RaisesPythonRuntimeErrorOnCreate(_AlwaysAvailableBackend):
    def create(self, *, dataset_mounts: dict[str, str], timeout_seconds: float) -> str:
        raise PythonRuntimeError("sandbox image not found")


def test_a_generic_exception_during_create_marks_the_runtime_error_not_stuck_starting(
    db_session: Session,
) -> None:
    service = PythonExecutionService(
        db_session, settings=_TEST_SETTINGS, backend=_RaisesGenericExceptionOnCreate()
    )
    with contextlib.suppress(Exception):  # the resulting AppError isn't the point of this test
        service.create_runtime("__test_user__")

    runtime = db_session.query(PythonRuntime).filter(PythonRuntime.user_id == "__test_user__").one()
    assert runtime.status == PythonRuntimeStatus.ERROR
    assert "daemon connection reset" in runtime.error_message


def test_a_known_python_runtime_error_during_create_still_marks_the_runtime_error(
    db_session: Session,
) -> None:
    """Confirms the pre-existing, already-correct path still works after
    adding the broader except clause alongside it."""
    service = PythonExecutionService(
        db_session, settings=_TEST_SETTINGS, backend=_RaisesPythonRuntimeErrorOnCreate()
    )
    with contextlib.suppress(Exception):
        service.create_runtime("__test_user_2__")

    runtime = db_session.query(PythonRuntime).filter(PythonRuntime.user_id == "__test_user_2__").one()
    assert runtime.status == PythonRuntimeStatus.ERROR
    assert "sandbox image not found" in runtime.error_message


def test_reap_sweeps_a_runtime_stuck_at_starting_past_the_grace_period(db_session: Session) -> None:
    stuck = PythonRuntime(
        user_id="__test_user_3__",
        status=PythonRuntimeStatus.STARTING,
        timeout_seconds=10,
    )
    db_session.add(stuck)
    db_session.commit()
    # Backdate created_at past the grace period -- a real "creation crashed
    # long ago," not a request genuinely still in flight right now.
    db_session.query(PythonRuntime).filter(PythonRuntime.id == stuck.id).update(
        {"created_at": datetime.now(UTC) - timedelta(minutes=10)}
    )
    db_session.commit()

    service = PythonExecutionService(db_session, settings=_TEST_SETTINGS, backend=_AlwaysAvailableBackend())
    swept = service.reap_idle_runtimes()

    db_session.refresh(stuck)
    assert swept >= 1
    assert stuck.status == PythonRuntimeStatus.STOPPED


def test_reap_does_not_sweep_a_runtime_that_just_started(db_session: Session) -> None:
    fresh = PythonRuntime(user_id="__test_user_4__", status=PythonRuntimeStatus.STARTING, timeout_seconds=10)
    db_session.add(fresh)
    db_session.commit()

    service = PythonExecutionService(db_session, settings=_TEST_SETTINGS, backend=_AlwaysAvailableBackend())
    service.reap_idle_runtimes()

    db_session.refresh(fresh)
    assert fresh.status == PythonRuntimeStatus.STARTING
