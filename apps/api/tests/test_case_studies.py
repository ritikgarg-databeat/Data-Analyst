"""Integration tests for the Case Study Engine (Phase 8) — exercised through
the real API + a real SQLite-backed DB session, with a hand-built Case row
(content/cases/*.yaml authoring is a separate concern from the engine itself,
exactly like test_data_modeling.py doesn't depend on any authored dataset)."""

from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.case import Case

RUBRIC = [
    {
        "category": "Problem Framing",
        "weight": 50,
        "criteria": [
            {"criterion": "Identifies the revenue driver", "points": 100},
        ],
    },
    {
        "category": "Technical Analysis",
        "weight": 50,
        "is_technical": True,
        "criteria": [{"criterion": "Correct SQL", "points": 100}],
    },
]


def _make_case(db_session: Session, **overrides) -> Case:
    base = dict(
        slug=f"revenue-drop-investigation-{uuid.uuid4().hex[:8]}",
        title="Revenue Drop Investigation",
        category="BUSINESS_ANALYTICS",
        difficulty="INTERMEDIATE",
        estimated_minutes=90,
        stakeholder_name="Priya Shah",
        stakeholder_role="VP of Sales",
        problem_statement="Our revenue dropped last quarter and I don't know why.",
        objective="Figure out why revenue dropped and recommend an action.",
        constraints=[],
        available_datasets=["orders"],
        expected_deliverables=["business_findings", "recommendation"],
        learning_objectives=["Diagnose a revenue decline"],
        stages=["CLARIFY", "FRAME", "EXPLORE", "ANALYZE", "RECOMMEND", "SUBMIT"],
        required_exercise_slugs=[],
        tags=["revenue", "sql"],
        skills=["sql"],
        rubric=RUBRIC,
        hints=["Check whether the decline is broad or concentrated in one segment."],
        reference_solution={
            "summary": "Revenue dropped because of a single underperforming region.",
            "key_insights": ["Region X declined 40%"],
            "recommendation": "Reallocate marketing spend away from Region X.",
            "acceptable_alternatives": [],
        },
        version=1,
    )
    base.update(overrides)
    case = Case(**base)
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


@pytest.fixture
def case(db_session: Session) -> Generator[Case, None, None]:
    yield _make_case(db_session)


def _start(client: TestClient, slug: str) -> dict:
    response = client.post(f"/api/v1/cases/{slug}/start")
    assert response.status_code == 201, response.text
    return response.json()


class TestCaseCatalog:
    def test_case_detail_hides_solution_and_hints_text(self, client: TestClient, case: Case) -> None:
        response = client.get(f"/api/v1/cases/{case.slug}")
        assert response.status_code == 200
        body = response.json()
        assert "reference_solution" not in body
        assert "hints" not in body
        assert body["hint_count"] == 1
        assert "rubric" in body  # weights/criteria are shown; only the answer is hidden

    def test_list_cases_supports_category_and_search_filters(self, client: TestClient, case: Case) -> None:
        by_category = client.get("/api/v1/cases", params={"category": "BUSINESS_ANALYTICS"}).json()
        assert any(item["case"]["slug"] == case.slug for item in by_category)

        by_search = client.get("/api/v1/cases", params={"search": "revenue"}).json()
        assert any(item["case"]["slug"] == case.slug for item in by_search)

        no_match = client.get("/api/v1/cases", params={"search": "nonexistent-topic-xyz"}).json()
        assert not any(item["case"]["slug"] == case.slug for item in no_match)


class TestAttemptLifecycle:
    def test_start_attempt_sets_initial_state(self, client: TestClient, case: Case) -> None:
        attempt = _start(client, case.slug)
        assert attempt["status"] == "IN_PROGRESS"
        assert attempt["current_stage"] == "CLARIFY"
        assert attempt["case_version_snapshot"] == 1
        assert attempt["attempt_number"] == 1

    def test_starting_twice_resumes_the_same_attempt(self, client: TestClient, case: Case) -> None:
        first = _start(client, case.slug)
        second = _start(client, case.slug)
        assert first["id"] == second["id"]

    def test_stage_progression_and_time_tracking(self, client: TestClient, case: Case) -> None:
        attempt = _start(client, case.slug)
        attempt_id = attempt["id"]

        updated = client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/stage", json={"stage": "FRAME"}
        ).json()
        assert updated["current_stage"] == "FRAME"

        timed = client.post(
            f"/api/v1/cases/attempts/{attempt_id}/stage-time", json={"stage": "CLARIFY", "seconds": 120}
        ).json()
        assert timed["time_per_stage_seconds"]["CLARIFY"] == 120

        timed_again = client.post(
            f"/api/v1/cases/attempts/{attempt_id}/stage-time", json={"stage": "CLARIFY", "seconds": 30}
        ).json()
        assert timed_again["time_per_stage_seconds"]["CLARIFY"] == 150

    def test_clarification_framing_and_dataset_selection_are_saved(
        self, client: TestClient, case: Case
    ) -> None:
        attempt_id = _start(client, case.slug)["id"]

        clarified = client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/clarification",
            json={"questions": "Which region and channel drove the decline?"},
        ).json()
        assert "region" in clarified["clarification_questions"]

        framed = client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/framing",
            json={
                "framing": {
                    "problem": "Revenue declined 15% QoQ",
                    "objective": "Identify the driver and recommend a fix",
                    "primary_metric": "Total revenue",
                    "scope": "Last two quarters, all regions",
                    "hypotheses": "One region or channel underperformed",
                }
            },
        ).json()
        assert framed["problem_framing"]["primary_metric"] == "Total revenue"

        with_datasets = client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/datasets", json={"dataset_slugs": ["orders"]}
        ).json()
        assert with_datasets["selected_dataset_slugs"] == ["orders"]

    def test_hints_are_revealed_progressively_and_run_out(self, client: TestClient, case: Case) -> None:
        attempt_id = _start(client, case.slug)["id"]
        first_hint = client.post(f"/api/v1/cases/attempts/{attempt_id}/hint")
        assert first_hint.status_code == 200
        assert first_hint.json()["hints_used"] == 1
        assert "segment" in first_hint.json()["hint"]

        exhausted = client.post(f"/api/v1/cases/attempts/{attempt_id}/hint")
        assert exhausted.status_code >= 400  # only one hint was configured

    def test_submission_readiness_reflects_real_progress(self, client: TestClient, case: Case) -> None:
        attempt = _start(client, case.slug)
        attempt_id = attempt["id"]
        assert attempt["submission_readiness"]["problem_framed"] is False
        assert attempt["submission_readiness"]["findings_documented"] is False

        client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/framing",
            json={
                "framing": {
                    "problem": "p",
                    "objective": "o",
                    "primary_metric": "m",
                    "scope": "s",
                    "hypotheses": "h",
                }
            },
        )
        client.post(
            "/api/v1/findings",
            json={"case_attempt_id": attempt_id, "observation": "Region X declined sharply."},
        )

        refreshed = client.get(f"/api/v1/cases/attempts/{attempt_id}").json()
        assert refreshed["submission_readiness"]["problem_framed"] is True
        assert refreshed["submission_readiness"]["findings_documented"] is True
        assert refreshed["submission_readiness"]["recommendation_written"] is False

    def test_full_submission_scores_and_completes_the_attempt(self, client: TestClient, case: Case) -> None:
        attempt_id = _start(client, case.slug)["id"]

        client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/recommendation",
            json={
                "recommendation": {
                    "recommendation": "Reallocate spend from Region X",
                    "why": "Region X drove the decline",
                    "expected_impact": "Recover ~10% of lost revenue",
                    "risks": "Other regions may need more time to absorb spend",
                    "implementation_considerations": "Coordinate with regional sales leads",
                    "next_steps": "Pilot in one channel first",
                }
            },
        )
        client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/executive-summary",
            json={
                "executive_summary": {
                    "problem": "Revenue declined 15%",
                    "key_findings": "Region X drove the decline",
                    "business_impact": "~$500k quarterly",
                    "recommendation": "Reallocate spend from Region X",
                    "next_steps": "Pilot reallocation",
                }
            },
        )

        submitted = client.post(
            f"/api/v1/cases/attempts/{attempt_id}/submit",
            json={
                "rubric_selections": {"Problem Framing": ["Identifies the revenue driver"]},
            },
        )
        assert submitted.status_code == 200, submitted.text
        body = submitted.json()
        assert body["status"] == "COMPLETED"
        assert body["score"]["overall"] == 50.0  # Problem Framing 100% * 0.5 weight; Technical self-assessed at 0%
        assert body["completed_at"] is not None
        assert "what_went_well" in body["feedback"]

    def test_cannot_submit_the_same_attempt_twice(self, client: TestClient, case: Case) -> None:
        attempt_id = _start(client, case.slug)["id"]
        first = client.post(f"/api/v1/cases/attempts/{attempt_id}/submit", json={"rubric_selections": {}})
        assert first.status_code == 200
        second = client.post(f"/api/v1/cases/attempts/{attempt_id}/submit", json={"rubric_selections": {}})
        assert second.status_code >= 400

    def test_reveal_solution_gated_on_completion(self, client: TestClient, case: Case) -> None:
        attempt_id = _start(client, case.slug)["id"]
        blocked = client.post(f"/api/v1/cases/attempts/{attempt_id}/reveal-solution")
        assert blocked.status_code >= 400

        client.post(f"/api/v1/cases/attempts/{attempt_id}/submit", json={"rubric_selections": {}})
        revealed = client.post(f"/api/v1/cases/attempts/{attempt_id}/reveal-solution")
        assert revealed.status_code == 200
        assert revealed.json()["key_insights"] == ["Region X declined 40%"]

    def test_reflection_is_saved(self, client: TestClient, case: Case) -> None:
        attempt_id = _start(client, case.slug)["id"]
        response = client.patch(
            f"/api/v1/cases/attempts/{attempt_id}/reflection",
            json={
                "reflection": {
                    "what_learned": "Segment before concluding",
                    "what_difficult": "Isolating the driver",
                    "what_differently": "Would check seasonality first",
                    "skill_improved": "Root-cause analysis",
                    "what_review": "Time-series decomposition",
                }
            },
        )
        assert response.status_code == 200
        assert response.json()["reflection"]["what_learned"] == "Segment before concluding"


class TestVersioning:
    def test_attempt_freezes_the_case_version_it_was_scored_against(
        self, client: TestClient, db_session: Session, case: Case
    ) -> None:
        attempt = _start(client, case.slug)
        assert attempt["case_version_snapshot"] == 1

        # Simulate a later content edit bumping the case's version — an
        # in-progress attempt's snapshot must NOT change retroactively
        # (spec section 48 / this phase's data-integrity requirement).
        case.version = 2
        case.rubric = [{"category": "Different Rubric", "weight": 100, "criteria": []}]
        db_session.commit()

        refetched = client.get(f"/api/v1/cases/attempts/{attempt['id']}").json()
        assert refetched["case_version_snapshot"] == 1


class TestAdmin:
    def test_admin_list_includes_inactive_cases_and_toggle_works(
        self, client: TestClient, db_session: Session, case: Case
    ) -> None:
        inactive = _make_case(db_session, title="Inactive Case", is_active=False)

        listed = client.get("/api/v1/cases/admin").json()
        slugs = {c["slug"] for c in listed}
        assert case.slug in slugs
        assert inactive.slug in slugs
        inactive_entry = next(c for c in listed if c["slug"] == inactive.slug)
        assert inactive_entry["is_active"] is False

        # Deactivated cases are hidden from the learner-facing catalog.
        public_slugs = {item["case"]["slug"] for item in client.get("/api/v1/cases").json()}
        assert inactive.slug not in public_slugs

        activated = client.patch(f"/api/v1/cases/admin/{inactive.id}", json={"is_active": True})
        assert activated.status_code == 200
        assert activated.json()["is_active"] is True


class TestOwnership:
    def test_attempt_for_nonexistent_case_is_not_found(self, client: TestClient) -> None:
        response = client.post("/api/v1/cases/not-a-real-slug/start")
        assert response.status_code == 404

    def test_getting_an_unknown_attempt_is_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/cases/attempts/does-not-exist")
        assert response.status_code == 404
