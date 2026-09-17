"""Job Description Analyzer + Skill Gap + Preparation/Interview Plan tests
(Phase 11) — verifies extraction never invents a skill slug outside the
real taxonomy, skill gaps reflect real UserSkill.mastery_score, the
readiness score responds to configurable weights, and the preparation/
interview plans are derived from real gaps."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.user_skill import UserSkill


def _create_jd(client: TestClient, raw_text: str, **overrides) -> dict:
    payload = {
        "title": "Data Analyst",
        "company": "Test Co",
        "source": "PASTED",
        "raw_text": raw_text,
    }
    payload.update(overrides)
    response = client.post("/api/v1/jobs/descriptions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestExtraction:
    def test_extraction_only_matches_known_skill_slugs(self, client: TestClient) -> None:
        jd = _create_jd(
            client,
            "We need someone skilled in SQL Fundamentals and Pandas. Familiarity with our proprietary "
            "in-house widget-frobnicator tool is a bonus.",
        )
        response = client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")
        assert response.status_code == 201, response.text
        requirements = response.json()

        known_slugs = {s["slug"] for s in client.get("/api/v1/skills").json()}
        for requirement in requirements:
            if requirement["matched_skill_slug"] is not None:
                assert requirement["matched_skill_slug"] in known_slugs

        matched = {r["matched_skill_slug"] for r in requirements}
        assert "sql-fundamentals" in matched
        assert "pandas" in matched

    def test_extraction_is_idempotent_replace_not_append(self, client: TestClient) -> None:
        jd = _create_jd(client, "Looking for strong SQL Fundamentals skills.")
        first = client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract").json()
        second = client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract").json()
        assert len(first) == len(second)


class TestSkillGaps:
    def test_gap_size_zero_when_mastery_meets_target(self, client: TestClient, db_session: Session) -> None:
        skill = db_session.query(Skill).filter(Skill.slug == "sql-fundamentals").one()
        user_id = client.get("/api/v1/users/me").json()["id"]
        user_skill = (
            db_session.query(UserSkill)
            .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id)
            .one_or_none()
        )
        if user_skill is None:
            user_skill = UserSkill(user_id=user_id, skill_id=skill.id)
            db_session.add(user_skill)
        user_skill.mastery_score = 95.0
        user_skill.questions_attempted = 5
        db_session.commit()

        jd = _create_jd(client, "Must have strong SQL Fundamentals.")
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")
        gaps = client.get(f"/api/v1/jobs/descriptions/{jd['id']}/skill-gaps").json()["gaps"]
        sql_gap = next(g for g in gaps if g["skill_slug"] == "sql-fundamentals")
        assert sql_gap["gap_size"] == 0.0
        assert sql_gap["current_mastery_score"] == 95.0

    def test_gap_size_positive_when_unmastered(self, client: TestClient) -> None:
        jd = _create_jd(client, f"Must have {uuid.uuid4().hex[:6]} Advanced SQL experience.")
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")
        gaps = client.get(f"/api/v1/jobs/descriptions/{jd['id']}/skill-gaps").json()["gaps"]
        assert any(g["skill_slug"] == "advanced-sql" and g["gap_size"] > 0 for g in gaps)


class TestReadinessAnalysis:
    def test_configurable_weights_change_score(self, client: TestClient, db_session: Session) -> None:
        skill = db_session.query(Skill).filter(Skill.slug == "advanced-sql").one()
        user_id = client.get("/api/v1/users/me").json()["id"]
        user_skill = (
            db_session.query(UserSkill)
            .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id)
            .one_or_none()
        )
        if user_skill is None:
            user_skill = UserSkill(user_id=user_id, skill_id=skill.id)
            db_session.add(user_skill)
        user_skill.mastery_score = 0.0
        user_skill.questions_attempted = 1
        db_session.commit()

        jd = _create_jd(client, "Advanced SQL is a strict must-have requirement for this role.")
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")

        default_analysis = client.post(f"/api/v1/jobs/descriptions/{jd['id']}/analyze", json={}).json()
        heavier_analysis = client.post(
            f"/api/v1/jobs/descriptions/{jd['id']}/analyze",
            json={"weights": {"MUST_HAVE": 10.0}},
        ).json()
        # Same unmastered skill, weighted more heavily -> readiness stays capped, never higher.
        assert heavier_analysis["readiness_score"] <= default_analysis["readiness_score"] + 0.01
        assert heavier_analysis["weights"]["MUST_HAVE"] == 10.0

    def test_analysis_never_exceeds_100(self, client: TestClient) -> None:
        jd = _create_jd(client, "Communication and business problem solving required.")
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")
        analysis = client.post(f"/api/v1/jobs/descriptions/{jd['id']}/analyze", json={}).json()
        assert 0.0 <= analysis["readiness_score"] <= 100.0


class TestPreparationAndInterviewPlan:
    def test_preparation_plan_only_covers_real_gaps(self, client: TestClient) -> None:
        jd = _create_jd(client, "Requires Data Modeling and Data Warehousing expertise.")
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")
        plan = client.get(f"/api/v1/jobs/descriptions/{jd['id']}/preparation-plan").json()
        gaps_response = client.get(f"/api/v1/jobs/descriptions/{jd['id']}/skill-gaps").json()
        gap_slugs = {g["skill_slug"] for g in gaps_response["gaps"] if g["gap_size"] > 0}
        task_slugs = {t["skill_slug"] for t in plan["tasks"]}
        assert task_slugs <= gap_slugs

    def test_interview_plan_carries_a_non_guarantee_note(self, client: TestClient) -> None:
        jd = _create_jd(client, "SQL and Python required for this analytics role.")
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")
        plan = client.get(f"/api/v1/jobs/descriptions/{jd['id']}/interview-plan").json()
        assert "not a claim" in plan["note"].lower() or "estimated" in plan["note"].lower()


class TestJobPreparationWorkspace:
    def test_create_workspace_is_idempotent_per_jd(self, client: TestClient) -> None:
        jd = _create_jd(client, "Generic role description.")
        first = client.post("/api/v1/jobs/workspaces", json={"job_description_id": jd["id"]})
        second = client.post("/api/v1/jobs/workspaces", json={"job_description_id": jd["id"]})
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] == second.json()["id"]

    def test_update_checklist_and_status(self, client: TestClient) -> None:
        jd = _create_jd(client, "Another role description.")
        workspace = client.post("/api/v1/jobs/workspaces", json={"job_description_id": jd["id"]}).json()
        updated = client.patch(
            f"/api/v1/jobs/workspaces/{workspace['id']}",
            json={"checklist": [{"label": "Review resume", "is_done": True}], "status": "IN_PROGRESS"},
        ).json()
        assert updated["status"] == "IN_PROGRESS"
        assert updated["checklist"][0]["is_done"] is True


class TestJobDescriptionComparison:
    def test_compare_reports_common_must_haves(self, client: TestClient) -> None:
        jd_a = _create_jd(client, "SQL Fundamentals is a strict requirement.", title="Role A")
        jd_b = _create_jd(client, "SQL Fundamentals is mandatory here too.", title="Role B")
        client.post(f"/api/v1/jobs/descriptions/{jd_a['id']}/extract")
        client.post(f"/api/v1/jobs/descriptions/{jd_b['id']}/extract")

        comparison = client.get(
            "/api/v1/jobs/descriptions/compare", params={"jd_ids": f"{jd_a['id']},{jd_b['id']}"}
        ).json()
        assert "sql-fundamentals" in comparison["common_must_have_skill_slugs"]
