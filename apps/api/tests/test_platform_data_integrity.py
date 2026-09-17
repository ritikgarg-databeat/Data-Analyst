"""Data Integrity Audit tests (Phase 12) — the endpoint must always
succeed (read-only) and report every check by name, never silently skip
one."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestDataIntegrity:
    def test_endpoint_returns_every_check(self, client: TestClient) -> None:
        response = client.get("/api/v1/platform/data-integrity")
        assert response.status_code == 200
        body = response.json()
        names = {c["name"] for c in body["checks"]}
        assert "skills.slug (duplicates)" in names
        assert "exercise_attempts.exercise_id" in names
        assert len(body["checks"]) >= 10

    def test_all_ok_matches_the_individual_checks(self, client: TestClient) -> None:
        body = client.get("/api/v1/platform/data-integrity").json()
        assert body["all_ok"] == all(c["orphaned_count"] == 0 for c in body["checks"])
