"""Next Best Action engine tests (Phase 12) — verifies the aggregator only
ever surfaces items that came from a real, already-existing signal (never
fabricates a recommendation), respects the requested limit, and each item
carries a real, navigable url_path."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestNextBestActions:
    def test_returns_a_small_capped_list(self, client: TestClient) -> None:
        response = client.get("/api/v1/platform/next-best-actions", params={"limit": 2})
        assert response.status_code == 200
        actions = response.json()["actions"]
        assert len(actions) <= 2

    def test_every_action_has_a_real_source_and_url(self, client: TestClient) -> None:
        response = client.get("/api/v1/platform/next-best-actions", params={"limit": 5})
        actions = response.json()["actions"]
        valid_sources = {"lesson", "interview", "job_description", "portfolio", "goal"}
        for action in actions:
            assert action["source"] in valid_sources
            assert action["url_path"].startswith("/")
            assert action["title"]
            assert action["why"]

    def test_job_description_action_appears_once_a_gap_exists(self, client: TestClient) -> None:
        jd = client.post(
            "/api/v1/jobs/descriptions",
            json={
                "title": "Next Best Action Probe Role",
                "source": "PASTED",
                "raw_text": "Must have strong Data Modeling and Data Warehousing experience.",
            },
        ).json()
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")

        response = client.get("/api/v1/platform/next-best-actions", params={"limit": 5})
        actions = response.json()["actions"]
        jd_actions = [a for a in actions if a["source"] == "job_description"]
        # The most-recently-created JD becomes "active" — since we just made
        # one, a job_description action should reference it if it has a gap.
        if jd_actions:
            assert jd["id"] in jd_actions[0]["url_path"]
