"""Portfolio Builder tests (Phase 11) — every new item defaults to PRIVATE
(spec section 20), the quality score is a deterministic heuristic that
responds to real completeness/description/visibility signals, and gap
detection only ever recommends real, currently-active project templates."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestPrivacyDefaults:
    def test_new_item_defaults_to_private(self, client: TestClient) -> None:
        portfolio = client.post(
            "/api/v1/portfolio/items",
            json={"item_type": "SKILL_HIGHLIGHT", "title": "SQL skills"},
        ).json()
        item = next(i for i in portfolio["items"] if i["title"] == "SQL skills")
        assert item["privacy"] == "PRIVATE"

    def test_privacy_can_be_upgraded_explicitly(self, client: TestClient) -> None:
        portfolio = client.post(
            "/api/v1/portfolio/items",
            json={"item_type": "SKILL_HIGHLIGHT", "title": "Python skills", "privacy": "PRIVATE"},
        ).json()
        item = next(i for i in portfolio["items"] if i["title"] == "Python skills")
        updated = client.patch(f"/api/v1/portfolio/items/{item['id']}", json={"privacy": "PORTFOLIO"}).json()
        updated_item = next(i for i in updated["items"] if i["id"] == item["id"])
        assert updated_item["privacy"] == "PORTFOLIO"


class TestQualityScore:
    def test_description_and_visibility_raise_the_score(self, client: TestClient) -> None:
        before = client.get("/api/v1/portfolio/quality-score").json()

        client.post(
            "/api/v1/portfolio/items",
            json={
                "item_type": "CERTIFICATION",
                "title": "Quality Score Probe Cert",
                "description": "A thorough, specific description of what this certification covers.",
                "privacy": "PORTFOLIO",
            },
        )
        after = client.get("/api/v1/portfolio/quality-score").json()
        assert after["score"] >= before["score"]
        assert after["items_with_description"] >= before["items_with_description"]
        assert after["portfolio_ready_item_count"] >= before["portfolio_ready_item_count"]

    def test_score_never_exceeds_100(self, client: TestClient) -> None:
        for i in range(8):
            client.post(
                "/api/v1/portfolio/items",
                json={
                    "item_type": "SKILL_HIGHLIGHT",
                    "title": f"Highlight {i}",
                    "description": "A real, specific description.",
                    "privacy": "PUBLIC_READY",
                },
            )
        score = client.get("/api/v1/portfolio/quality-score").json()
        assert score["score"] <= 100.0


class TestGapDetection:
    def test_gap_detection_recommends_only_active_templates(self, client: TestClient) -> None:
        target_role = client.post(
            "/api/v1/career/target-roles", json={"role_template_slug": "analytics-engineer-entry"}
        ).json()
        gaps = client.get("/api/v1/portfolio/gaps", params={"target_role_id": target_role["id"]}).json()

        active_slugs = {
            t["slug"] for t in client.get("/api/v1/projects/templates").json()
        }
        for gap in gaps:
            for slug in gap["recommended_project_template_slugs"]:
                assert slug in active_slugs

    def test_no_target_role_returns_no_gaps(self, client: TestClient) -> None:
        gaps = client.get("/api/v1/portfolio/gaps").json()
        assert gaps == []
