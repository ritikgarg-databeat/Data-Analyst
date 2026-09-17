from fastapi.testclient import TestClient


def test_list_datasets_returns_seeded_dataset(client: TestClient) -> None:
    response = client.get("/api/v1/datasets")

    assert response.status_code == 200
    datasets = response.json()
    slugs = {d["slug"] for d in datasets}
    # A subset check, not equality: the shared test-session database may also
    # contain datasets created by Dataset Hub import tests (test_dataset_import.py
    # etc.) that run in the same session — this test only cares that the two
    # seeded datasets are present and well-formed.
    assert {"orders-sample", "ecommerce"}.issubset(slugs)

    orders_sample = next(d for d in datasets if d["slug"] == "orders-sample")
    assert orders_sample["metadata"]["columns"] == [
        "order_id",
        "customer_id",
        "order_date",
        "status",
        "order_total",
    ]


def test_get_dataset_by_slug(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/orders-sample")

    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 10
    assert body["file_format"] == "csv"


def test_get_unknown_dataset_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/does-not-exist")

    assert response.status_code == 404


def test_sql_table_only_dataset_still_reports_its_tables(client: TestClient) -> None:
    """"ecommerce"/"saas-product" only ever get SqlTable rows, never a Phase 5
    DatasetTable — GET /datasets/{slug} must still surface their real tables
    (not an empty list), or the Visualization/Product Analytics table pickers
    have no way to select anything but an implicit backend default (Phase 6
    regression — see DatasetService.to_schema)."""
    response = client.get("/api/v1/datasets/ecommerce")

    assert response.status_code == 200
    body = response.json()
    table_names = {t["table_name"] for t in body["tables"]}
    assert {"orders", "customers", "payments"}.issubset(table_names)
    orders_table = next(t for t in body["tables"] if t["table_name"] == "orders")
    assert orders_table["row_count"] is not None
    assert orders_table["size_bytes"] is None


def test_saas_product_dataset_tables_are_ordered_and_include_events(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/saas-product")

    assert response.status_code == 200
    body = response.json()
    table_names = [t["table_name"] for t in body["tables"]]
    assert "events" in table_names
    display_orders = [t["display_order"] for t in body["tables"]]
    assert display_orders == sorted(display_orders)
