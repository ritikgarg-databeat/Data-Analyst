from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import Base, get_db
from app.db.seed import seed
from app.dependencies.services import get_python_execution_service, get_python_exercise_service
from app.main import app
from app.python_lab.service import PythonExecutionService
from app.services.python_exercise_service import PythonExerciseService
from tests.python_lab_fakes import InProcessKernelBackend

# Generous relative to the production default (4) — several independent
# integration tests each create their own runtime(s) against the SAME
# session-scoped DB without necessarily destroying them, since exercising
# cleanup isn't every test's concern. The concurrency limit itself has its
# own dedicated test (test_python_lab_security.py).
_TEST_SETTINGS = Settings(python_lab_max_concurrent_runtimes=100)

# A single shared in-memory SQLite connection for the whole test session.
# StaticPool keeps the same underlying connection alive across sessions,
# which in-memory SQLite otherwise doesn't support.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        seed(session)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _override_get_db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def python_backend() -> InProcessKernelBackend:
    """A fresh, real-but-unisolated sandbox backend per test — see
    tests/python_lab_fakes.py's module docstring for exactly what this does
    and doesn't verify."""
    return InProcessKernelBackend()


@pytest.fixture(autouse=True)
def _override_python_lab_backend(python_backend: InProcessKernelBackend) -> Generator[None, None, None]:
    def _execution_service() -> PythonExecutionService:
        session = TestingSessionLocal()
        return PythonExecutionService(session, settings=_TEST_SETTINGS, backend=python_backend)

    def _exercise_service() -> PythonExerciseService:
        session = TestingSessionLocal()
        service = PythonExerciseService(session)
        service.execution_service = PythonExecutionService(
            session, settings=_TEST_SETTINGS, backend=python_backend
        )
        return service

    app.dependency_overrides[get_python_execution_service] = _execution_service
    app.dependency_overrides[get_python_exercise_service] = _exercise_service
    yield
    del app.dependency_overrides[get_python_execution_service]
    del app.dependency_overrides[get_python_exercise_service]


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def dataset_dirs_cleanup() -> Generator[list[str], None, None]:
    """Dataset Hub tests (test_dataset_import.py etc.) write real files
    under data/raw|processed|datasets/<slug>/ (see app/dataset_hub/paths.py)
    since import must stay repo-relative — see app/sql/paths.py's
    REPO_ROOT/resolve_repo_path, which every DatasetTable/SqlTable.file_path
    is resolved against. Tests append the slug(s) they created here; this
    fixture removes those directories on teardown, pass or fail, so
    repeated local test runs never accumulate stray fixture data."""
    import shutil

    from app.dataset_hub.paths import DATASETS_DIR, PROCESSED_DIR, RAW_DIR

    slugs: list[str] = []
    yield slugs
    for slug in slugs:
        for base in (RAW_DIR, PROCESSED_DIR, DATASETS_DIR):
            shutil.rmtree(base / slug, ignore_errors=True)
