"""Real dbt Lab integration tests — every test here shells out to the actual
`dbt` CLI (see app/dbt_lab/runner.py) against the real project at repo-root
`dbt/`, reading the real ecommerce CSV fixtures. Nothing here is mocked:
these tests are only meaningful if dbt-core/dbt-duckdb are actually
installed (see apps/api/pyproject.toml) and the dbt project at `dbt/` is
valid. A scratch DuckDB warehouse file (not data/warehouse/dev.duckdb) keeps
these tests isolated from a developer's own manual dbt Lab session.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.dbt_lab.paths import resolve_target_dir
from app.dbt_lab.service import DbtLabService
from app.dependencies.services import get_dbt_lab_service
from app.main import app
from app.models.user import User
from tests.conftest import TestingSessionLocal

_SCRATCH_DIR = Path(__file__).resolve().parent / "_scratch_dbt"
_SCRATCH_WAREHOUSE = _SCRATCH_DIR / "test_dev.duckdb"


@pytest.fixture(scope="module", autouse=True)
def _dbt_lab_scratch_warehouse() -> Generator[None, None, None]:
    _SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    test_settings = Settings(dbt_warehouse_path=str(_SCRATCH_WAREHOUSE))

    def _service() -> DbtLabService:
        return DbtLabService(TestingSessionLocal(), settings=test_settings)

    app.dependency_overrides[get_dbt_lab_service] = _service
    yield
    del app.dependency_overrides[get_dbt_lab_service]
    shutil.rmtree(_SCRATCH_DIR, ignore_errors=True)


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def _run_full_dbt_build(client: TestClient) -> None:
    """Runs the real project once (build + docs generate) before any test in
    this module — every other test just inspects the results, instead of
    each re-running the (~several-second) dbt invocation itself."""
    build = client.post("/api/v1/dbt/run", json={"command": "build"})
    assert build.status_code == 201, build.text
    docs = client.post("/api/v1/dbt/run", json={"command": "docs generate"})
    assert docs.status_code == 201, docs.text


def test_build_ran_successfully_against_real_duckdb(client: TestClient) -> None:
    runs = client.get("/api/v1/dbt/runs").json()
    commands = {r["command"] for r in runs}
    assert "build" in commands
    assert "docs generate" in commands
    build_run = next(r for r in runs if r["command"] == "build")
    assert build_run["status"] == "SUCCESS"
    assert build_run["summary"]["node_count"] > 0
    with TestingSessionLocal() as db:
        user_id = db.scalar(select(User.id).where(User.email == "analyst@example.com"))
    assert user_id is not None
    target_dir = resolve_target_dir(user_id)
    assert target_dir.joinpath("manifest.json").exists()
    assert target_dir.joinpath("catalog.json").exists()


def test_project_tree_lists_real_files_by_layer(client: TestClient) -> None:
    tree = client.get("/api/v1/dbt/project-tree").json()
    by_category = {item["category"]: item["name"] for item in tree}
    names = {item["name"] for item in tree}
    assert "stg_orders" in names
    assert "fct_orders" in names
    assert "customer_segment_snapshot" in names
    assert any(item["category"] == "staging" and item["name"] == "stg_orders" for item in tree)
    assert any(item["category"] == "marts" and item["name"] == "fct_orders" for item in tree)
    assert by_category  # non-empty


def test_lineage_graph_reflects_real_dependencies(client: TestClient) -> None:
    graph = client.get("/api/v1/dbt/lineage").json()
    nodes_by_name = {n["name"]: n for n in graph["nodes"]}

    assert "stg_orders" in nodes_by_name
    assert nodes_by_name["stg_orders"]["layer"] == "staging"
    assert nodes_by_name["fct_orders"]["layer"] == "marts"

    fct_orders_id = nodes_by_name["fct_orders"]["unique_id"]
    stg_orders_id = nodes_by_name["stg_orders"]["unique_id"]
    edge_pairs = {(e["from_unique_id"], e["to_unique_id"]) for e in graph["edges"]}
    assert (stg_orders_id, fct_orders_id) in edge_pairs

    # A source table feeds stg_orders.
    source_node = next(n for n in graph["nodes"] if n["resource_type"] == "source" and n["name"] == "orders")
    assert (source_node["unique_id"], stg_orders_id) in edge_pairs


def test_docs_include_column_types_and_descriptions(client: TestClient) -> None:
    docs = client.get("/api/v1/dbt/docs").json()
    fct_orders = next(d for d in docs if d["name"] == "fct_orders")
    assert fct_orders["materialized"] == "table"
    column_names = {c["name"] for c in fct_orders["columns"]}
    assert "order_id" in column_names
    assert "gross_margin_pct" in column_names
    order_id_col = next(c for c in fct_orders["columns"] if c["name"] == "order_id")
    assert order_id_col["data_type"] is not None  # from catalog.json, since a real query ran
    assert len(fct_orders["test_unique_ids"]) > 0  # unique + not_null tests attached


def test_test_results_report_real_pass_fail(client: TestClient) -> None:
    # Every dbt subcommand overwrites run_results.json, including the
    # `docs generate` the module fixture ran last — re-run `dbt test` so the
    # artifact this reads actually reflects a real test execution.
    test_run = client.post("/api/v1/dbt/run", json={"command": "test"})
    assert test_run.status_code == 201, test_run.text

    results = client.get("/api/v1/dbt/test-results").json()
    assert len(results) > 50  # 57 generic tests + 1 singular test, per the project's schema files
    statuses = {r["status"] for r in results}
    assert statuses == {"pass"}
    singular = next(r for r in results if r["name"] == "assert_no_negative_revenue")
    assert singular["status"] == "pass"


def test_run_with_selector_scopes_to_one_model(client: TestClient) -> None:
    response = client.post("/api/v1/dbt/run", json={"command": "run", "selector": "stg_customers"})
    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "SUCCESS"
    assert run["selector"] == "stg_customers"
    assert run["summary"]["node_count"] == 1


def test_a_broken_model_reports_as_failed_not_a_crash(client: TestClient, tmp_path: Path) -> None:
    """A model that fails to compile should come back as a normal FAILED
    DbtRun (an educational, recoverable state) — never as a 500 or an
    unhandled exception."""
    from app.dbt_lab.paths import DBT_PROJECT_DIR

    broken_model = DBT_PROJECT_DIR / "models" / "marts" / "_broken_test_model.sql"
    broken_model.write_text("select * from this_table_does_not_exist_anywhere\n", encoding="utf-8")
    try:
        response = client.post(
            "/api/v1/dbt/run", json={"command": "run", "selector": "_broken_test_model"}
        )
        assert response.status_code == 201
        run = response.json()
        assert run["status"] == "FAILED"
        assert run["summary"]["result_counts"].get("error", 0) >= 1
    finally:
        broken_model.unlink(missing_ok=True)


def test_run_not_found_for_other_user_raises_404(client: TestClient) -> None:
    response = client.get("/api/v1/dbt/runs/does-not-exist")
    assert response.status_code == 404
