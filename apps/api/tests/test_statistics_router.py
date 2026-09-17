"""HTTP-level tests for /api/v1/statistics/* — thin wiring checks; the real
numerical correctness is covered by tests/test_stats_engine.py."""

import pytest
from fastapi.testclient import TestClient


def test_summary_from_raw_values(client: TestClient) -> None:
    response = client.post("/api/v1/statistics/summary", json={"values": [1, 2, 3, 4, 5]})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    assert body["mean"] == 3.0
    assert "methodology" in body


def test_summary_requires_values_or_dataset(client: TestClient) -> None:
    response = client.post("/api/v1/statistics/summary", json={})
    assert response.status_code == 422


def test_run_independent_t_test(client: TestClient) -> None:
    response = client.post(
        "/api/v1/statistics/test",
        json={"test_type": "independent_t", "sample_a": [1, 2, 3, 2, 1], "sample_b": [20, 21, 19, 22, 20]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reject_null"] is True
    assert body["test_type"] == "independent_t"


def test_run_test_unknown_type_returns_400(client: TestClient) -> None:
    response = client.post("/api/v1/statistics/test", json={"test_type": "not_a_real_test"})
    assert response.status_code == 400


def test_correlation_from_raw_arrays(client: TestClient) -> None:
    response = client.post(
        "/api/v1/statistics/correlation",
        json={"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10], "method": "pearson"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["statistic"] == 1.0


def test_summary_from_dataset_column(client: TestClient) -> None:
    response = client.post(
        "/api/v1/statistics/summary",
        json={"dataset": {"dataset_id": "ecommerce", "table_name": "payments", "column": "amount"}},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 3699


def test_summary_dataset_unknown_column_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/statistics/summary",
        json={"dataset": {"dataset_id": "ecommerce", "table_name": "payments", "column": "not_a_column"}},
    )
    assert response.status_code == 404


def test_regression_from_raw_arrays(client: TestClient) -> None:
    response = client.post(
        "/api/v1/statistics/regression",
        json={"features": {"x": [1, 2, 3, 4, 5]}, "y": [2, 4, 6, 8, 10]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["r_squared"] == pytest.approx(1.0)
    assert body["coefficients"][0]["value"] == pytest.approx(2.0)
