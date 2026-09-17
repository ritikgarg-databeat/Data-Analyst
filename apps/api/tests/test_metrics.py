"""Tests for the Metrics Library (Phase 6, spec section 42) — seeded from
database/seeds/metrics.yaml via app.db.seed._seed_metrics."""

from fastapi.testclient import TestClient


def test_list_metrics_returns_seeded_entries(client: TestClient) -> None:
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    metrics = response.json()
    slugs = {m["slug"] for m in metrics}
    assert {"revenue", "cac", "ltv", "dau", "mrr", "churn"}.issubset(slugs)
    assert len(metrics) >= 20


def test_get_metric_by_slug(client: TestClient) -> None:
    response = client.get("/api/v1/metrics/cac")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Customer Acquisition Cost (CAC)"
    assert "ltv" in body["related_metrics"]
    assert len(body["interview_questions"]) >= 1


def test_get_unknown_metric_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/metrics/does-not-exist")
    assert response.status_code == 404


def test_filter_metrics_by_category(client: TestClient) -> None:
    response = client.get("/api/v1/metrics?category=product")
    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) > 0
    assert all(m["category"] == "product" for m in metrics)


def test_search_metrics_by_query(client: TestClient) -> None:
    response = client.get("/api/v1/metrics?q=conversion")
    assert response.status_code == 200
    metrics = response.json()
    assert any("conversion" in m["name"].lower() or "conversion" in m["definition"].lower() for m in metrics)
