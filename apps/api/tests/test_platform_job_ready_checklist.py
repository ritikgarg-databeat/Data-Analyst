"""Job-Ready Checklist tests (Phase 12) — every item must be a real,
evidence-based boolean, never fabricated."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestJobReadyChecklist:
    def test_returns_the_six_expected_groups(self, client: TestClient) -> None:
        response = client.get("/api/v1/platform/job-ready-checklist")
        assert response.status_code == 200
        body = response.json()
        group_names = {g["group"] for g in body["groups"]}
        assert group_names == {
            "Technical", "Analytics", "Data Stack", "Applied", "Interview", "Career",
        }

    def test_ready_count_matches_the_real_items(self, client: TestClient) -> None:
        body = client.get("/api/v1/platform/job-ready-checklist").json()
        all_items = [item for g in body["groups"] for item in g["items"]]
        assert body["total_count"] == len(all_items)
        assert body["ready_count"] == sum(1 for i in all_items if i["ready"])

    def test_every_item_is_a_plain_boolean(self, client: TestClient) -> None:
        body = client.get("/api/v1/platform/job-ready-checklist").json()
        for group in body["groups"]:
            for item in group["items"]:
                assert isinstance(item["ready"], bool)
                assert item["label"]
