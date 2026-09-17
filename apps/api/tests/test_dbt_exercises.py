"""Real dbt exercise grading tests — every submission here is graded by
actually writing SQL into the real dbt project and running `dbt build
--select <model>` (see app/services/dbt_exercise_service.py). Nothing is
mocked or text-matched: a submission passes because dbt itself says the
model built and its tests passed.

Uses a scratch warehouse (like test_dbt_lab.py) so this never touches a
developer's own data/warehouse/dev.duckdb, but the exercise models
themselves reference real upstream staging/marts models via ref()/source(),
so the scratch warehouse must be bootstrapped with a full `dbt build` first —
exactly like a real learner who's already run the dbt Lab before attempting
exercises.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.content.loader import load_exercise_file
from app.core.config import Settings
from app.dbt_lab.paths import DBT_PROJECT_DIR
from app.dbt_lab.runner import run_dbt
from app.dependencies.services import get_dbt_exercise_service
from app.main import app
from app.services.dbt_exercise_service import DbtExerciseService
from tests.conftest import TestingSessionLocal

_SCRATCH_DIR = Path(__file__).resolve().parent / "_scratch_dbt_exercises"
_SCRATCH_WAREHOUSE = _SCRATCH_DIR / "test_dev.duckdb"
_EXERCISES_DIR = DBT_PROJECT_DIR / "models" / "exercises"

_SLUGS = [
    "ex-stg-active-products",
    "ex-ref-order-customer-join",
    "ex-orders-per-channel-summary",
    "ex-order-status-check",
    "ex-order-items-relationship",
    "ex-customers-segment-check",
    "ex-product-margin-pct",
    "ex-category-rollup",
    "ex-payments-by-method-summary",
    "ex-customer-segment-current",
]


@pytest.fixture(scope="module", autouse=True)
def _dbt_exercise_scratch_warehouse() -> Generator[None, None, None]:
    _SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    test_settings = Settings(dbt_warehouse_path=str(_SCRATCH_WAREHOUSE))

    def _service() -> DbtExerciseService:
        return DbtExerciseService(TestingSessionLocal(), settings=test_settings)

    app.dependency_overrides[get_dbt_exercise_service] = _service

    for stale in _EXERCISES_DIR.glob("*"):
        if stale.name != ".gitkeep":
            stale.unlink()
    bootstrap = run_dbt(["build"], settings=test_settings)
    assert bootstrap.returncode == 0, bootstrap.stdout + bootstrap.stderr

    yield

    del app.dependency_overrides[get_dbt_exercise_service]
    for stale in _EXERCISES_DIR.glob("*"):
        if stale.name != ".gitkeep":
            stale.unlink()
    shutil.rmtree(_SCRATCH_DIR, ignore_errors=True)


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("slug", _SLUGS)
def test_starter_sql_fails_and_solution_passes_for_real(slug: str, client: TestClient) -> None:
    content = client.get(f"/api/v1/dbt/exercises/{slug}")
    assert content.status_code == 200, content.text
    starter_sql = content.json()["starter_sql"]
    assert starter_sql, f"{slug} has no starter_sql"

    starter_response = client.post(f"/api/v1/dbt/exercises/{slug}/submit", json={"submitted_sql": starter_sql})
    assert starter_response.status_code == 200, starter_response.text
    starter_body = starter_response.json()
    assert starter_body["passed"] is False, f"{slug}: starter_sql unexpectedly passed"
    assert starter_body["explanation"] is None  # never revealed on failure


@pytest.mark.parametrize("slug", _SLUGS)
def test_solution_passes_for_real(slug: str, client: TestClient) -> None:
    # `solution` is server-side-only (never exposed via GET /dbt/exercises/{slug} —
    # see test_dbt_exercise_content_never_leaks_the_solution below), so this
    # test reads it directly off disk, the same way the grading service's own
    # content-loading does.
    content = load_exercise_file(f"content/exercises/modern-data-stack/{slug}.yaml")
    assert content.solution, f"{slug} has no solution"

    response = client.post(f"/api/v1/dbt/exercises/{slug}/submit", json={"submitted_sql": content.solution})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["model_built"] is True, f"{slug}: solution failed to build — {body['log']}"
    assert body["passed"] is True, f"{slug}: solution didn't pass — {body['test_outcomes']}"
    assert body["score"] == 100.0
    assert body["explanation"]  # revealed once passed


@pytest.mark.parametrize("hook_snippet", ["pre_hook", "pre-hook", "POST_HOOK", "post-hook"])
def test_a_pre_or_post_hook_config_is_rejected_before_it_ever_reaches_dbt(
    hook_snippet: str, client: TestClient
) -> None:
    """Regression test: a submitted model is written verbatim into a real
    dbt model file and built via a real `dbt build` subprocess, with no
    guard against `{{ config(pre_hook=...) }}`/`post_hook` -- arbitrary raw
    SQL dbt executes outside any wrapping, unlike the SQL Lab's explicit
    write/DDL/admin denylist for the same shape of risk."""
    malicious_sql = f'{{{{ config({hook_snippet}="DROP TABLE IF EXISTS something") }}}}\nSELECT 1 AS x'
    response = client.post(
        "/api/v1/dbt/exercises/ex-stg-active-products/submit", json={"submitted_sql": malicious_sql}
    )
    assert response.status_code == 400
    assert "hook" in response.json()["error"]["message"].lower()


def test_dbt_exercise_content_never_leaks_the_solution(client: TestClient) -> None:
    response = client.get("/api/v1/dbt/exercises/ex-stg-active-products")
    assert response.status_code == 200
    body = response.json()
    assert "solution" not in body
    assert "dbt_schema_yml" not in body


def test_rejecting_a_non_dbt_exercise_slug(client: TestClient) -> None:
    response = client.get("/api/v1/dbt/exercises/aov-query")  # a real SQL exercise
    assert response.status_code == 400
