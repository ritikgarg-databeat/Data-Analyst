"""Real Data Quality Lab tests — every rule actually executes against the
real, seeded `ecommerce` dataset via DuckDB (see app/sql/registry.py); no
rule outcome here is fabricated or mocked."""

from fastapi.testclient import TestClient


def _ecommerce_dataset_id(client: TestClient) -> str:
    return client.get("/api/v1/datasets/ecommerce").json()["id"]


def _create_rule(client: TestClient, **kwargs) -> dict:
    dataset_id = kwargs.pop("dataset_id", None) or _ecommerce_dataset_id(client)
    payload = {"dataset_id": dataset_id, **kwargs}
    response = client.post("/api/v1/data-quality/rules", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_not_null_rule_passes_on_a_clean_column(client: TestClient) -> None:
    rule = _create_rule(
        client, table_name="orders", column_name="customer_id", rule_type="NOT_NULL", name="orders customer_id"
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "PASS"
    assert run["details"]["violation_count"] == 0


def test_unique_rule_passes_on_a_primary_key(client: TestClient) -> None:
    rule = _create_rule(client, table_name="orders", column_name="order_id", rule_type="UNIQUE")
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "PASS"


def test_unique_rule_fails_on_a_column_with_repeats(client: TestClient) -> None:
    rule = _create_rule(client, table_name="orders", column_name="customer_id", rule_type="UNIQUE")
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "FAIL"
    assert run["details"]["violation_count"] > 0


def test_accepted_values_rule_passes_with_real_values(client: TestClient) -> None:
    rule = _create_rule(
        client,
        table_name="orders",
        column_name="status",
        rule_type="ACCEPTED_VALUES",
        config={"values": ["refunded", "pending", "completed", "cancelled"]},
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "PASS"


def test_accepted_values_rule_fails_with_an_incomplete_list(client: TestClient) -> None:
    rule = _create_rule(
        client,
        table_name="orders",
        column_name="status",
        rule_type="ACCEPTED_VALUES",
        config={"values": ["completed"]},
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "FAIL"
    assert run["details"]["violation_count"] > 0


def test_relationship_rule_passes_for_real_referential_integrity(client: TestClient) -> None:
    rule = _create_rule(
        client,
        table_name="order_items",
        column_name="order_id",
        rule_type="RELATIONSHIP",
        config={"to_table": "orders", "to_column": "order_id"},
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "PASS"


def test_relationship_rule_fails_against_the_wrong_table(client: TestClient) -> None:
    rule = _create_rule(
        client,
        table_name="order_items",
        column_name="order_id",
        rule_type="RELATIONSHIP",
        config={"to_table": "products", "to_column": "product_id"},
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "FAIL"


def test_row_count_rule_passes_within_range(client: TestClient) -> None:
    rule = _create_rule(
        client, table_name="orders", rule_type="ROW_COUNT", config={"min_rows": 4000, "max_rows": 5000}
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "PASS"
    assert run["details"]["row_count"] == 4205


def test_row_count_rule_fails_outside_range(client: TestClient) -> None:
    rule = _create_rule(client, table_name="orders", rule_type="ROW_COUNT", config={"min_rows": 999_999})
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "FAIL"


def test_min_max_rule_passes_within_bounds(client: TestClient) -> None:
    rule = _create_rule(
        client, table_name="order_items", column_name="quantity", rule_type="MIN_MAX", config={"min": 0, "max": 1000}
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "PASS"


def test_min_max_rule_fails_when_bounds_are_too_narrow(client: TestClient) -> None:
    rule = _create_rule(
        client, table_name="order_items", column_name="quantity", rule_type="MIN_MAX", config={"max": 0}
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "FAIL"


def test_freshness_rule_uses_configurable_as_of_date(client: TestClient) -> None:
    query_result = client.post(
        "/api/v1/sql/execute",
        json={"engine": "duckdb", "database": "ecommerce", "query": "SELECT MAX(order_date) FROM orders"},
    ).json()
    max_order_date = query_result["rows"][0][0]

    rule = _create_rule(
        client,
        table_name="orders",
        column_name="order_date",
        rule_type="FRESHNESS",
        config={"as_of": max_order_date, "max_age_hours": 24 * 400},
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "PASS"


def test_freshness_rule_fails_when_max_age_is_too_strict(client: TestClient) -> None:
    # A reference date safely after the real (historical) order data, so the
    # "latest order" is guaranteed to look stale relative to it.
    rule = _create_rule(
        client,
        table_name="orders",
        column_name="order_date",
        rule_type="FRESHNESS",
        config={"as_of": "2030-01-01T00:00:00", "max_age_hours": 1},
    )
    run = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run").json()
    assert run["status"] == "FAIL"


def test_row_count_with_no_threshold_reports_error_not_a_silent_pass(client: TestClient) -> None:
    """Regression test: ROW_COUNT's `ok` expression was unconditionally True
    when neither min_rows nor max_rows was configured — a rule the UI itself
    allowed saving (both fields are labeled optional) reported a
    false-confidence PASS forever, regardless of actual row count."""
    rule = _create_rule(client, table_name="orders", rule_type="ROW_COUNT", config={})
    response = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run")
    assert response.status_code == 201
    assert response.json()["status"] == "ERROR"


def test_freshness_with_no_max_age_reports_error_not_a_silent_pass(client: TestClient) -> None:
    """Regression test: FRESHNESS's `ok` expression was unconditionally True
    when max_age_hours wasn't configured — same false-confidence-PASS gap
    as ROW_COUNT above."""
    rule = _create_rule(
        client, table_name="orders", column_name="order_date", rule_type="FRESHNESS", config={}
    )
    response = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run")
    assert response.status_code == 201
    assert response.json()["status"] == "ERROR"


def test_freshness_against_a_non_date_column_reports_error_not_a_crash(client: TestClient) -> None:
    """Regression test: running FRESHNESS against a numeric column (a real,
    easy mistake — the UI's column-name input is free text, not scoped to
    date-typed columns) used to raise an unhandled ValueError from
    `datetime.fromisoformat`, surfacing as a raw 500 instead of a graceful
    ERROR run."""
    rule = _create_rule(
        client,
        table_name="orders",
        column_name="customer_id",
        rule_type="FRESHNESS",
        config={"max_age_hours": 24},
    )
    response = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run")
    assert response.status_code == 201
    assert response.json()["status"] == "ERROR"


def test_misconfigured_rule_reports_error_not_a_crash(client: TestClient) -> None:
    rule = _create_rule(client, table_name="orders", column_name="status", rule_type="ACCEPTED_VALUES", config={})
    response = client.post(f"/api/v1/data-quality/rules/{rule['id']}/run")
    assert response.status_code == 201
    assert response.json()["status"] == "ERROR"


def test_run_history_is_persisted_and_listed(client: TestClient) -> None:
    rule = _create_rule(client, table_name="orders", rule_type="ROW_COUNT", config={"min_rows": 1})
    client.post(f"/api/v1/data-quality/rules/{rule['id']}/run")
    client.post(f"/api/v1/data-quality/rules/{rule['id']}/run")
    runs = client.get(f"/api/v1/data-quality/rules/{rule['id']}/runs").json()
    assert len(runs) >= 2


def test_rule_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/data-quality/rules/does-not-exist")
    assert response.status_code == 404


def test_delete_rule_removes_it(client: TestClient) -> None:
    rule = _create_rule(client, table_name="orders", rule_type="ROW_COUNT", config={"min_rows": 1})
    delete_response = client.delete(f"/api/v1/data-quality/rules/{rule['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/data-quality/rules/{rule['id']}").status_code == 404
