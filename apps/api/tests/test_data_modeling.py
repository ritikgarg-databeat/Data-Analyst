"""Data Modeler / Architecture Diagram Builder / Pipeline Playground tests —
one shared graph schema and validation engine (see app/models/data_model.py,
app/data_modeling/validation.py), exercised through the real API + a real
SQLite-backed DB session (no mocking)."""

from fastapi.testclient import TestClient


def _create_model(client: TestClient, model_kind: str = "DIMENSIONAL", name: str = "Test Model") -> dict:
    response = client.post("/api/v1/modeling/models", json={"name": name, "model_kind": model_kind})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_list_get_update_delete_model(client: TestClient) -> None:
    created = _create_model(client, name="Ecommerce Star Schema")
    assert created["model_kind"] == "DIMENSIONAL"
    assert created["tables"] == []

    listed = client.get("/api/v1/modeling/models", params={"model_kind": "DIMENSIONAL"}).json()
    assert any(m["id"] == created["id"] for m in listed)

    fetched = client.get(f"/api/v1/modeling/models/{created['id']}").json()
    assert fetched["name"] == "Ecommerce Star Schema"

    updated = client.patch(f"/api/v1/modeling/models/{created['id']}", json={"name": "Renamed"}).json()
    assert updated["name"] == "Renamed"

    delete_response = client.delete(f"/api/v1/modeling/models/{created['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/modeling/models/{created['id']}").status_code == 404


def test_save_graph_creates_tables_and_relationships(client: TestClient) -> None:
    model = _create_model(client, name="Orders Star")
    graph = {
        "tables": [
            {
                "key": "orders",
                "name": "fct_orders",
                "table_type": "FACT",
                "grain": "1 row = 1 order",
                "columns": [
                    {"name": "order_id", "is_primary_key": True},
                    {
                        "name": "customer_id",
                        "is_foreign_key": True,
                        "references_table": "dim_customers",
                        "references_column": "customer_id",
                    },
                    {"name": "gross_revenue", "data_type": "double"},
                ],
            },
            {
                "key": "customers",
                "name": "dim_customers",
                "table_type": "DIMENSION",
                "columns": [{"name": "customer_id", "is_primary_key": True}, {"name": "email"}],
            },
        ],
        "relationships": [
            {
                "from_key": "orders",
                "to_key": "customers",
                "from_column": "customer_id",
                "to_column": "customer_id",
                "relationship_type": "MANY_TO_ONE",
            }
        ],
    }
    response = client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert len(saved["tables"]) == 2
    assert len(saved["relationships"]) == 1
    fct_orders = next(t for t in saved["tables"] if t["name"] == "fct_orders")
    dim_customers = next(t for t in saved["tables"] if t["name"] == "dim_customers")
    rel = saved["relationships"][0]
    assert rel["from_table_id"] == fct_orders["id"]
    assert rel["to_table_id"] == dim_customers["id"]


def test_save_graph_with_unknown_relationship_key_returns_400(client: TestClient) -> None:
    model = _create_model(client)
    graph = {
        "tables": [{"key": "a", "name": "table_a", "columns": []}],
        "relationships": [{"from_key": "a", "to_key": "does-not-exist"}],
    }
    response = client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    assert response.status_code == 400


def test_validate_clean_model_has_no_findings(client: TestClient) -> None:
    model = _create_model(client, name="Clean Model")
    graph = {
        "tables": [
            {
                "key": "orders",
                "name": "fct_orders",
                "table_type": "FACT",
                "grain": "1 row = 1 order",
                "columns": [{"name": "order_id", "is_primary_key": True}],
            }
        ],
        "relationships": [],
    }
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    assert result["findings"] == []
    assert result["error_count"] == 0


def test_validate_flags_missing_primary_key(client: TestClient) -> None:
    model = _create_model(client)
    graph = {"tables": [{"key": "a", "name": "no_pk_table", "columns": [{"name": "some_column"}]}]}
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    codes = {f["code"] for f in result["findings"]}
    assert "missing_primary_key" in codes
    assert all(f["severity"] == "warning" for f in result["findings"] if f["code"] == "missing_primary_key")


def test_validate_flags_duplicate_columns(client: TestClient) -> None:
    model = _create_model(client)
    graph = {
        "tables": [
            {
                "key": "a",
                "name": "dup_table",
                "columns": [{"name": "id", "is_primary_key": True}, {"name": "id"}],
            }
        ]
    }
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    codes = {f["code"] for f in result["findings"]}
    assert "duplicate_column" in codes


def test_validate_flags_foreign_key_to_unknown_table(client: TestClient) -> None:
    model = _create_model(client)
    graph = {
        "tables": [
            {
                "key": "a",
                "name": "orders",
                "columns": [
                    {"name": "order_id", "is_primary_key": True},
                    {"name": "customer_id", "is_foreign_key": True, "references_table": "customers"},
                ],
            }
        ]
    }
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    codes = {f["code"] for f in result["findings"]}
    assert "foreign_key_unknown_table" in codes


def test_validate_flags_fact_table_without_grain(client: TestClient) -> None:
    model = _create_model(client)
    graph = {
        "tables": [
            {"key": "a", "name": "fct_no_grain", "table_type": "FACT", "columns": [{"name": "id", "is_primary_key": True}]}
        ]
    }
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    codes = {f["code"] for f in result["findings"]}
    assert "fact_table_missing_grain" in codes


def test_validate_flags_dimension_with_measure_like_column(client: TestClient) -> None:
    model = _create_model(client)
    graph = {
        "tables": [
            {
                "key": "a",
                "name": "dim_customers",
                "table_type": "DIMENSION",
                "columns": [
                    {"name": "customer_id", "is_primary_key": True},
                    {"name": "total_revenue", "data_type": "float"},
                ],
            }
        ]
    }
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    codes = {f["code"] for f in result["findings"]}
    assert "dimension_looks_like_measure" in codes


def test_validate_flags_circular_relationship_in_pipeline_as_error(client: TestClient) -> None:
    model = _create_model(client, model_kind="PIPELINE", name="Circular Pipeline")
    graph = {
        "tables": [
            {"key": "a", "name": "stage_a", "table_type": "SOURCE", "columns": []},
            {"key": "b", "name": "stage_b", "table_type": "TRANSFORM", "columns": []},
        ],
        "relationships": [
            {"from_key": "a", "to_key": "b", "relationship_type": "DEPENDS_ON"},
            {"from_key": "b", "to_key": "a", "relationship_type": "DEPENDS_ON"},
        ],
    }
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    cycle_findings = [f for f in result["findings"] if f["code"] == "circular_relationship"]
    assert len(cycle_findings) == 1
    assert cycle_findings[0]["severity"] == "error"


def test_validate_flags_circular_relationship_in_architecture_as_warning(client: TestClient) -> None:
    model = _create_model(client, model_kind="ARCHITECTURE", name="Circular Architecture")
    graph = {
        "tables": [
            {"key": "a", "name": "service_a", "table_type": "SERVICE", "columns": []},
            {"key": "b", "name": "service_b", "table_type": "SERVICE", "columns": []},
        ],
        "relationships": [
            {"from_key": "a", "to_key": "b", "relationship_type": "FLOW"},
            {"from_key": "b", "to_key": "a", "relationship_type": "FLOW"},
        ],
    }
    client.put(f"/api/v1/modeling/models/{model['id']}/graph", json=graph)
    result = client.post(f"/api/v1/modeling/models/{model['id']}/validate").json()
    cycle_findings = [f for f in result["findings"] if f["code"] == "circular_relationship"]
    assert len(cycle_findings) == 1
    assert cycle_findings[0]["severity"] == "warning"


def test_model_not_found_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/modeling/models/does-not-exist").status_code == 404
