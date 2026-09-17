"""Integration tests for the SQL Lab execution stack — DuckDB connection,
dataset/table discovery, schema/preview introspection, and query execution
against the real generated `ecommerce` CSVs (see app/sql/generate_dataset.py)."""

from fastapi.testclient import TestClient


def test_list_engines_reports_duckdb_available_and_postgres_unavailable(client: TestClient) -> None:
    response = client.get("/api/v1/sql/engines")

    assert response.status_code == 200
    engines = {e["name"]: e for e in response.json()}
    assert engines["duckdb"]["is_available"] is True
    assert engines["postgres"]["is_available"] is False
    assert engines["postgres"]["reason"]


def test_list_databases_includes_the_ecommerce_dataset(client: TestClient) -> None:
    response = client.get("/api/v1/sql/databases")

    assert response.status_code == 200
    databases = {d["name"]: d for d in response.json()}
    assert "ecommerce" in databases
    assert databases["ecommerce"]["engine"] == "duckdb"
    assert databases["ecommerce"]["table_count"] == 8


def test_list_tables_returns_all_ecommerce_tables_with_grain_and_counts(client: TestClient) -> None:
    response = client.get("/api/v1/sql/databases/ecommerce/tables")

    assert response.status_code == 200
    tables = {t["table_name"]: t for t in response.json()}
    assert set(tables) == {
        "categories",
        "products",
        "customers",
        "marketing_campaigns",
        "sessions",
        "orders",
        "order_items",
        "payments",
    }
    assert tables["orders"]["row_count"] == 4205
    assert tables["orders"]["grain"]
    assert tables["payments"]["column_count"] == 6


def test_unknown_database_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/sql/databases/does-not-exist/tables")

    assert response.status_code == 404


def test_get_table_schema_reports_columns_and_types(client: TestClient) -> None:
    response = client.get("/api/v1/sql/databases/ecommerce/tables/orders/schema")

    assert response.status_code == 200
    body = response.json()
    columns = {c["name"]: c["type"] for c in body["columns"]}
    assert columns["order_id"] == "BIGINT"
    assert columns["status"] == "VARCHAR"
    assert body["row_count"] == 4205


def test_unknown_table_schema_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/sql/databases/ecommerce/tables/nope/schema")

    assert response.status_code == 404


def test_preview_table_returns_sample_rows_and_null_counts(client: TestClient) -> None:
    response = client.get("/api/v1/sql/databases/ecommerce/tables/sessions/preview")

    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 12000
    assert body["sample_row_count"] == 20
    assert len(body["rows"]) == 20
    # sessions.customer_id is genuinely nullable in the generated dataset (anonymous visits).
    assert body["null_counts"]["customer_id"] > 0


def test_execute_a_real_aggregate_query_against_the_ecommerce_dataset(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sql/execute",
        json={
            "engine": "duckdb",
            "database": "ecommerce",
            "query": "SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY n DESC",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["engine"] == "duckdb"
    assert [c["name"] for c in body["columns"]] == ["status", "n"]
    assert body["rows"][0] == ["completed", 3441]
    assert body["row_count"] == 4
    assert body["truncated"] is False
    assert body["error"] is None


def test_execute_a_multi_table_join_reconciles_payments_to_order_items(client: TestClient) -> None:
    # payments.amount is generated as the exact sum of that order's order_items
    # line revenue ((unit_price - discount) * quantity) — a hard invariant of
    # the dataset generator, worth locking in as a regression test.
    response = client.post(
        "/api/v1/sql/execute",
        json={
            "engine": "duckdb",
            "database": "ecommerce",
            "query": """
                SELECT COUNT(*) FROM payments p
                JOIN (
                    SELECT order_id, ROUND(SUM((unit_price - discount) * quantity), 2) AS computed_total
                    FROM order_items GROUP BY order_id
                ) oi ON oi.order_id = p.order_id
                WHERE ABS(p.amount - oi.computed_total) > 0.01
            """,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["rows"] == [[0]]


def test_execute_truncates_results_at_the_configured_row_limit(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sql/execute",
        json={"engine": "duckdb", "database": "ecommerce", "query": "SELECT * FROM sessions"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["truncated"] is True
    assert body["row_count"] == 1000  # sql_lab_row_limit default


def test_execute_and_history_round_trip(client: TestClient) -> None:
    exec_response = client.post(
        "/api/v1/sql/execute",
        json={"engine": "duckdb", "database": "ecommerce", "query": "SELECT COUNT(*) FROM categories"},
    )
    assert exec_response.status_code == 200

    history_response = client.get("/api/v1/sql/history?limit=1")
    assert history_response.status_code == 200
    latest = history_response.json()[0]
    assert latest["database"] == "ecommerce"
    assert latest["status"] == "success"
    assert latest["query"].strip() == "SELECT COUNT(*) FROM categories"


def test_saved_query_and_workspace_crud(client: TestClient) -> None:
    workspace = client.post(
        "/api/v1/sql/workspaces", json={"name": "Scratch", "engine": "duckdb", "database": "ecommerce"}
    ).json()

    saved = client.post(
        "/api/v1/sql/saved",
        json={
            "title": "Orders by status",
            "query": "SELECT status, COUNT(*) FROM orders GROUP BY status",
            "engine": "duckdb",
            "database": "ecommerce",
            "workspace_id": workspace["id"],
        },
    ).json()
    assert saved["workspace_id"] == workspace["id"]

    listed = client.get(f"/api/v1/sql/saved?workspace_id={workspace['id']}").json()
    assert any(q["id"] == saved["id"] for q in listed)

    updated = client.patch(f"/api/v1/sql/saved/{saved['id']}", json={"title": "Orders by status (v2)"}).json()
    assert updated["title"] == "Orders by status (v2)"

    delete_response = client.delete(f"/api/v1/sql/saved/{saved['id']}")
    assert delete_response.status_code == 204
