"""Integration tests for Findings/Hypotheses/Evidence (Phase 8) — the shared
structures used by both the Case Study Engine and the Project Engine (see
app/models/finding.py's docstring), exercised through the real API against a
hand-built CaseAttempt (ownership/ordering/evidence-linking is independent of
any specific Case content)."""

from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.case import Case, CaseAttempt
from app.services.user_service import UserService


@pytest.fixture
def attempt_id(db_session: Session) -> Generator[str, None, None]:
    case = Case(
        slug=f"finding-test-case-{uuid.uuid4().hex[:8]}",
        title="Finding Test Case",
        category="BUSINESS_ANALYTICS",
        difficulty="BEGINNER",
        stakeholder_name="Test Stakeholder",
        stakeholder_role="Manager",
        problem_statement="A problem",
        objective="An objective",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    user_id = UserService(db_session).get_current_user().id
    attempt = CaseAttempt(user_id=user_id, case_id=case.id, case_version_snapshot=1)
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)
    yield attempt.id


class TestFindingsCrud:
    def test_create_list_update_delete_finding(self, client: TestClient, attempt_id: str) -> None:
        created = client.post(
            "/api/v1/findings",
            json={"case_attempt_id": attempt_id, "observation": "Revenue is down 15% QoQ."},
        )
        assert created.status_code == 201, created.text
        finding_id = created.json()["id"]
        assert created.json()["evidence"] == []

        listed = client.get("/api/v1/findings", params={"case_attempt_id": attempt_id}).json()
        assert any(f["id"] == finding_id for f in listed)

        updated = client.patch(
            f"/api/v1/findings/{finding_id}",
            json={"impact": "High — affects quarterly targets", "confidence": "HIGH"},
        )
        assert updated.status_code == 200
        assert updated.json()["impact"] == "High — affects quarterly targets"
        assert updated.json()["confidence"] == "HIGH"

        deleted = client.delete(f"/api/v1/findings/{finding_id}")
        assert deleted.status_code == 204
        after = client.get("/api/v1/findings", params={"case_attempt_id": attempt_id}).json()
        assert not any(f["id"] == finding_id for f in after)

    def test_findings_are_ordered_by_creation(self, client: TestClient, attempt_id: str) -> None:
        client.post("/api/v1/findings", json={"case_attempt_id": attempt_id, "observation": "First"})
        client.post("/api/v1/findings", json={"case_attempt_id": attempt_id, "observation": "Second"})
        listed = client.get("/api/v1/findings", params={"case_attempt_id": attempt_id}).json()
        assert [f["observation"] for f in listed] == ["First", "Second"]

    def test_must_specify_exactly_one_owner(self, client: TestClient, attempt_id: str) -> None:
        neither = client.post("/api/v1/findings", json={"observation": "orphaned"})
        assert neither.status_code >= 400

        both = client.post(
            "/api/v1/findings",
            json={"case_attempt_id": attempt_id, "project_id": "some-project", "observation": "conflicting"},
        )
        assert both.status_code >= 400

    def test_cannot_create_finding_for_nonexistent_attempt(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/findings", json={"case_attempt_id": "does-not-exist", "observation": "x"}
        )
        assert response.status_code == 404


class TestFindingEvidence:
    def test_add_evidence_denormalizes_a_snapshot(self, client: TestClient, attempt_id: str) -> None:
        finding_id = client.post(
            "/api/v1/findings", json={"case_attempt_id": attempt_id, "observation": "Region X declined."}
        ).json()["id"]

        evidence = client.post(
            f"/api/v1/findings/{finding_id}/evidence",
            json={
                "evidence_type": "SQL_QUERY",
                "ref_id": "some-query-history-id",
                "label": "Revenue by region query",
                "snapshot": "SELECT region, SUM(revenue) FROM orders GROUP BY region;",
            },
        )
        assert evidence.status_code == 201, evidence.text
        assert evidence.json()["snapshot"].startswith("SELECT region")

        finding = client.get("/api/v1/findings", params={"case_attempt_id": attempt_id}).json()[0]
        assert len(finding["evidence"]) == 1

    def test_evidence_survives_deletion_of_the_referenced_row_by_design(
        self, client: TestClient, attempt_id: str
    ) -> None:
        # There's no real SqlQueryHistory row behind ref_id here at all — the
        # point is that Evidence never joins against it; `snapshot` alone is
        # enough for a finding to stay meaningful (spec section 60).
        finding_id = client.post(
            "/api/v1/findings", json={"case_attempt_id": attempt_id, "observation": "obs"}
        ).json()["id"]
        evidence = client.post(
            f"/api/v1/findings/{finding_id}/evidence",
            json={
                "evidence_type": "STATISTIC",
                "ref_id": "a-deleted-row-id",
                "label": "t-test result",
                "snapshot": "p=0.03, effect size=0.4",
            },
        ).json()
        assert evidence["ref_id"] == "a-deleted-row-id"
        assert evidence["snapshot"] == "p=0.03, effect size=0.4"

    def test_delete_evidence(self, client: TestClient, attempt_id: str) -> None:
        finding_id = client.post(
            "/api/v1/findings", json={"case_attempt_id": attempt_id, "observation": "obs"}
        ).json()["id"]
        evidence_id = client.post(
            f"/api/v1/findings/{finding_id}/evidence",
            json={"evidence_type": "CHART", "ref_id": None, "label": "Revenue trend chart", "snapshot": None},
        ).json()["id"]
        response = client.delete(f"/api/v1/evidence/{evidence_id}")
        assert response.status_code == 204


class TestHypothesisTracker:
    def test_create_and_transition_hypothesis_status(self, client: TestClient, attempt_id: str) -> None:
        created = client.post(
            "/api/v1/hypotheses",
            json={"case_attempt_id": attempt_id, "statement": "The decline is concentrated in Region X."},
        )
        assert created.status_code == 201
        hypothesis_id = created.json()["id"]
        assert created.json()["status"] == "UNCHECKED"

        investigating = client.patch(
            f"/api/v1/hypotheses/{hypothesis_id}", json={"status": "INVESTIGATING"}
        )
        assert investigating.json()["status"] == "INVESTIGATING"

        supported = client.patch(
            f"/api/v1/hypotheses/{hypothesis_id}",
            json={"status": "SUPPORTED", "evidence_text": "Region X down 40% vs. 2% elsewhere"},
        )
        assert supported.json()["status"] == "SUPPORTED"
        assert "40%" in supported.json()["evidence_text"]

    def test_hypothesis_can_carry_evidence(self, client: TestClient, attempt_id: str) -> None:
        hypothesis_id = client.post(
            "/api/v1/hypotheses", json={"case_attempt_id": attempt_id, "statement": "H1"}
        ).json()["id"]
        evidence = client.post(
            f"/api/v1/hypotheses/{hypothesis_id}/evidence",
            json={"evidence_type": "DATASET", "ref_id": None, "label": "orders dataset", "snapshot": None},
        )
        assert evidence.status_code == 201

        listed = client.get("/api/v1/hypotheses", params={"case_attempt_id": attempt_id}).json()
        found = next(h for h in listed if h["id"] == hypothesis_id)
        assert len(found["evidence"]) == 1

    def test_delete_hypothesis(self, client: TestClient, attempt_id: str) -> None:
        hypothesis_id = client.post(
            "/api/v1/hypotheses", json={"case_attempt_id": attempt_id, "statement": "to be deleted"}
        ).json()["id"]
        response = client.delete(f"/api/v1/hypotheses/{hypothesis_id}")
        assert response.status_code == 204
        listed = client.get("/api/v1/hypotheses", params={"case_attempt_id": attempt_id}).json()
        assert not any(h["id"] == hypothesis_id for h in listed)
