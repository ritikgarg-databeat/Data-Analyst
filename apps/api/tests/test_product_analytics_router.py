"""HTTP-level tests for the Phase 6 product-analytics dataset endpoints
(raw-schema/funnel/cohort-retention) against the real seeded "saas-product"
SQL Lab database — which, like "ecommerce", is registered as a plain
SqlTable-only dataset (no DatasetProfile), so these endpoints must not
depend on one (see app/services/dataset_analysis_service.py)."""

from fastapi.testclient import TestClient


def test_raw_schema_works_without_a_dataset_profile(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/saas-product/analysis/raw-schema?table=events")
    assert response.status_code == 200
    body = response.json()
    assert body["table_name"] == "events"
    column_names = {c["column_name"] for c in body["columns"]}
    assert {"user_id", "signup_date", "event_name", "event_timestamp"}.issubset(column_names)


def test_raw_schema_unknown_dataset_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/does-not-exist/analysis/raw-schema")
    assert response.status_code == 404


def test_funnel_endpoint_against_real_saas_product_data(client: TestClient) -> None:
    response = client.get(
        "/api/v1/datasets/saas-product/analysis/funnel"
        "?table=events&user_col=user_id&event_col=event_name&steps=signup,activated,engaged,upgraded"
    )
    assert response.status_code == 200
    body = response.json()
    steps = {s["step"]: s for s in body["steps"]}
    assert set(steps) == {"signup", "activated", "engaged", "upgraded"}
    # A real funnel: each step's user count is non-increasing.
    counts = [steps[s]["users"] for s in ["signup", "activated", "engaged", "upgraded"]]
    assert counts == sorted(counts, reverse=True)
    assert steps["signup"]["users"] > 0


def test_funnel_requires_at_least_two_steps(client: TestClient) -> None:
    response = client.get(
        "/api/v1/datasets/saas-product/analysis/funnel?table=events&user_col=user_id&event_col=event_name&steps=signup"
    )
    assert response.status_code == 400


def test_cohort_retention_against_real_saas_product_data(client: TestClient) -> None:
    response = client.get(
        "/api/v1/datasets/saas-product/analysis/cohort-retention"
        "?table=events&user_col=user_id&cohort_date_col=signup_date&activity_date_col=event_timestamp"
        "&granularity=month&periods=3"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["granularity"] == "month"
    assert len(body["cohorts"]) > 0
    first_cohort = body["cohorts"][0]
    assert first_cohort["cohort_size"] > 0
    assert first_cohort["retention_pct"][0] == 100.0


def test_cohort_retention_unknown_column_returns_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/datasets/saas-product/analysis/cohort-retention"
        "?table=events&user_col=not_a_column&cohort_date_col=signup_date&activity_date_col=event_timestamp"
    )
    assert response.status_code == 404
