"""HTTP-level tests for /api/v1/experiments/* — thin wiring checks; the real
numerical correctness is covered by tests/test_experimentation_engine.py."""

from fastapi.testclient import TestClient


def test_sample_size_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/experiments/sample-size",
        json={"baseline_conversion": 0.1, "expected_uplift_relative": 0.2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sample_size_per_variant"] > 0
    assert body["total_sample_size"] == body["sample_size_per_variant"] * 2


def test_power_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/experiments/power",
        json={"baseline_conversion": 0.1, "sample_size_per_variant": 2000, "expected_uplift_relative": 0.2},
    )
    assert response.status_code == 200
    assert 0 <= response.json()["achieved_power"] <= 1


def test_analyze_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/experiments/analyze",
        json={
            "control_users": 10000,
            "control_conversions": 1000,
            "treatment_users": 10000,
            "treatment_conversions": 1250,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_statistically_significant"] is True
    assert body["verdict"] == "Ship-worthy evidence"


def test_analyze_endpoint_rejects_invalid_counts(client: TestClient) -> None:
    response = client.post(
        "/api/v1/experiments/analyze",
        json={
            "control_users": 100,
            "control_conversions": 200,
            "treatment_users": 100,
            "treatment_conversions": 10,
        },
    )
    assert response.status_code == 400


def test_simulate_endpoint_is_deterministic(client: TestClient) -> None:
    payload = {
        "control_rate": 0.1,
        "treatment_rate": 0.15,
        "sample_size_per_variant": 500,
        "num_simulations": 100,
        "seed": 7,
    }
    r1 = client.post("/api/v1/experiments/simulate", json=payload)
    r2 = client.post("/api/v1/experiments/simulate", json=payload)
    assert r1.status_code == 200
    assert r1.json()["empirical_power"] == r2.json()["empirical_power"]
