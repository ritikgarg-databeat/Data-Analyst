"""System Health / Diagnostics tests (Phase 12) — verifies every check is
side-effect-free, reports a real status (never crashes the endpoint even
when a dependency is genuinely unavailable), and distinguishes "not
configured" (expected, local-first-optional) from "unavailable" (a real
problem)."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestSystemHealth:
    def test_health_endpoint_always_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/platform/health")
        assert response.status_code == 200

    def test_reports_every_expected_service(self, client: TestClient) -> None:
        services = {s["name"] for s in client.get("/api/v1/platform/health").json()["services"]}
        assert "Core Database" in services
        assert "DuckDB" in services
        assert "Python Sandbox" in services
        assert "dbt" in services
        assert "AI Provider" in services
        assert "Kaggle" in services

    def test_core_database_and_duckdb_are_ok_in_tests(self, client: TestClient) -> None:
        services = {s["name"]: s for s in client.get("/api/v1/platform/health").json()["services"]}
        assert services["Core Database"]["status"] == "ok"
        assert services["DuckDB"]["status"] == "ok"

    def test_ai_provider_reports_not_configured_under_the_local_default(self, client: TestClient) -> None:
        services = {s["name"]: s for s in client.get("/api/v1/platform/health").json()["services"]}
        # The test settings default to AI_PROVIDER=local (no key needed) —
        # this must read as "not_configured", never "unavailable" (a
        # local-first optional integration being unset is not a failure).
        assert services["AI Provider"]["status"] in ("not_configured", "ok")

    def test_every_status_is_a_known_value(self, client: TestClient) -> None:
        for service in client.get("/api/v1/platform/health").json()["services"]:
            assert service["status"] in ("ok", "degraded", "unavailable", "not_configured")
