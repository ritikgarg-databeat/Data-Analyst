"""Integration tests for the Python Lab execution stack — runtime lifecycle,
multi-cell state, dataset listing, history, and workspaces/cells — against
the real `PythonKernel` via `InProcessKernelBackend` (see
tests/python_lab_fakes.py for exactly what this does and doesn't verify)."""

from fastapi.testclient import TestClient


def test_availability_reports_the_fake_backend_as_available(client: TestClient) -> None:
    response = client.get("/api/v1/python/availability")
    assert response.status_code == 200
    assert response.json() == {"available": True, "reason": None}


def test_list_datasets_includes_ecommerce_tables_and_orders_sample(client: TestClient) -> None:
    response = client.get("/api/v1/python/datasets")
    assert response.status_code == 200
    files = response.json()
    labels_by_dataset: dict[str, list[str]] = {}
    for f in files:
        labels_by_dataset.setdefault(f["dataset_slug"], []).append(f["label"])
    assert "orders.csv" in labels_by_dataset["ecommerce"]
    assert any("orders_sample" in label for label in labels_by_dataset["orders-sample"])
    orders_file = next(f for f in files if f["dataset_slug"] == "ecommerce" and f["label"] == "orders.csv")
    assert orders_file["container_path"] == "/data/ecommerce/orders.csv"
    assert 'pd.read_csv("/data/ecommerce/orders.csv")' in orders_file["suggested_code"]


def test_create_execute_and_destroy_a_runtime(client: TestClient) -> None:
    created = client.post("/api/v1/python/runtimes").json()
    assert created["status"] == "READY"
    runtime_id = created["id"]

    exec_response = client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": "x = 21 * 2"})
    assert exec_response.status_code == 200
    body = exec_response.json()
    assert body["status"] == "success"
    x_var = next(v for v in body["variables"] if v["name"] == "x")
    assert x_var["value"] == 42

    delete_response = client.delete(f"/api/v1/python/runtimes/{runtime_id}")
    assert delete_response.status_code == 204


def test_variables_persist_across_separate_execute_calls_on_the_same_runtime(client: TestClient) -> None:
    runtime_id = client.post("/api/v1/python/runtimes").json()["id"]
    client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": "orders_count = 4205"})
    response = client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": "orders_count * 2"})
    assert response.json()["display_value"]["value"] == 8410


def test_pandas_execution_returns_a_dataframe_summary(client: TestClient) -> None:
    runtime_id = client.post("/api/v1/python/runtimes").json()["id"]
    code = "import pandas as pd\ndf = pd.read_csv('/data/ecommerce/products.csv')\ndf.head()"
    response = client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": code})
    body = response.json()
    assert body["status"] == "success"
    assert body["display_value"]["dataframe"]["row_count"] == 5


def test_restart_clears_variables_but_the_runtime_stays_usable(client: TestClient) -> None:
    runtime_id = client.post("/api/v1/python/runtimes").json()["id"]
    client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": "y = 5"})

    restart_response = client.post(f"/api/v1/python/runtimes/{runtime_id}/restart")
    assert restart_response.status_code == 200
    assert restart_response.json()["status"] == "READY"

    after = client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": "y"})
    assert after.json()["status"] == "error"
    assert after.json()["error"]["error_type"] == "NameError"


def test_a_runtime_error_is_returned_not_raised_as_an_http_error(client: TestClient) -> None:
    runtime_id = client.post("/api/v1/python/runtimes").json()["id"]
    response = client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": "1 / 0"})
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert response.json()["error"]["error_type"] == "ZeroDivisionError"


def test_execute_and_history_round_trip(client: TestClient) -> None:
    runtime_id = client.post("/api/v1/python/runtimes").json()["id"]
    client.post(f"/api/v1/python/runtimes/{runtime_id}/execute", json={"code": "print('history check')"})

    history = client.get("/api/v1/python/history?limit=1").json()
    assert history[0]["code"].strip() == "print('history check')"
    assert history[0]["status"] == "success"


def test_unknown_runtime_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/python/runtimes/does-not-exist")
    assert response.status_code == 404


class TestWorkspacesAndCells:
    def test_create_workspace_seeds_one_empty_cell(self, client: TestClient) -> None:
        workspace = client.post("/api/v1/python/workspaces", json={"name": "EDA scratch"}).json()
        cells = client.get(f"/api/v1/python/workspaces/{workspace['id']}/cells").json()
        assert len(cells) == 1
        assert cells[0]["code"] == ""

    def test_add_update_and_delete_a_cell(self, client: TestClient) -> None:
        workspace = client.post("/api/v1/python/workspaces", json={"name": "Marketing analysis"}).json()
        cell = client.post(
            f"/api/v1/python/workspaces/{workspace['id']}/cells", json={"code": "1 + 1"}
        ).json()

        updated = client.patch(
            f"/api/v1/python/workspaces/{workspace['id']}/cells/{cell['id']}", json={"code": "2 + 2"}
        ).json()
        assert updated["code"] == "2 + 2"

        delete_response = client.delete(f"/api/v1/python/workspaces/{workspace['id']}/cells/{cell['id']}")
        assert delete_response.status_code == 204

    def test_record_cell_result_persists_the_last_execution(self, client: TestClient) -> None:
        workspace = client.post("/api/v1/python/workspaces", json={"name": "Retention"}).json()
        runtime_id = client.post(f"/api/v1/python/runtimes?workspace_id={workspace['id']}").json()["id"]
        cells = client.get(f"/api/v1/python/workspaces/{workspace['id']}/cells").json()
        cell_id = cells[0]["id"]

        result = client.post(
            f"/api/v1/python/runtimes/{runtime_id}/execute",
            json={"code": "42", "workspace_id": workspace["id"]},
        ).json()
        record_response = client.post(
            f"/api/v1/python/workspaces/{workspace['id']}/cells/{cell_id}/result", json={"result": result}
        )
        assert record_response.status_code == 200
        assert record_response.json()["last_result"]["display_value"]["value"] == 42
        assert record_response.json()["last_executed_at"] is not None

    def test_delete_workspace_cascades_to_its_cells(self, client: TestClient) -> None:
        workspace = client.post("/api/v1/python/workspaces", json={"name": "Temp"}).json()
        delete_response = client.delete(f"/api/v1/python/workspaces/{workspace['id']}")
        assert delete_response.status_code == 204
        assert client.get(f"/api/v1/python/workspaces/{workspace['id']}").status_code == 404
