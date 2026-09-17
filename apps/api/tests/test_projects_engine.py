"""Integration tests for the Project Engine (Phase 8) — the Phase 5 minimal
project shell extended in place with templates, milestones, artifacts,
dataset usage, documentation/presentation, and rubric-based submission.
Exercised through the real API against a hand-built ProjectTemplate."""

from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import ProjectTemplate

RUBRIC = [
    {
        "category": "Data Quality Awareness",
        "weight": 30,
        "criteria": [{"criterion": "Flags missing values", "points": 100}],
    },
    {
        "category": "Business Impact",
        "weight": 70,
        "criteria": [{"criterion": "Quantifies revenue impact", "points": 100}],
    },
]


def _make_template(db_session: Session, **overrides) -> ProjectTemplate:
    base = dict(
        slug=f"ecommerce-analytics-{uuid.uuid4().hex[:8]}",
        title="E-commerce Analytics Platform",
        category="BUSINESS_ANALYTICS",
        business_context="A mid-size online retailer wants a full analytics buildout.",
        objective="Build a data model, analysis, and dashboard for the retailer.",
        requirements=["A dimensional data model", "A revenue-by-channel dashboard"],
        suggested_datasets=["orders", "customers"],
        milestones=[
            {"title": "Understand the Business", "description": "Talk to stakeholders"},
            {"title": "Data Discovery", "description": "Find relevant datasets"},
            {"title": "Data Model", "description": "Design the dimensional model"},
        ],
        required_skills=["sql", "data-modeling"],
        rubric=RUBRIC,
        learning_objectives=["End-to-end analytics delivery"],
        estimated_hours=6.0,
        tags=["ecommerce", "capstone"],
    )
    base.update(overrides)
    template = ProjectTemplate(**base)
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def template(db_session: Session) -> Generator[ProjectTemplate, None, None]:
    yield _make_template(db_session)


def _create_from_template(client: TestClient, slug: str) -> dict:
    response = client.post("/api/v1/projects/from-template", json={"template_slug": slug})
    assert response.status_code == 201, response.text
    return response.json()


class TestTemplateCatalog:
    def test_list_and_get_template(self, client: TestClient, template: ProjectTemplate) -> None:
        listed = client.get("/api/v1/projects/templates").json()
        assert any(t["slug"] == template.slug for t in listed)

        fetched = client.get(f"/api/v1/projects/templates/{template.slug}").json()
        assert fetched["title"] == "E-commerce Analytics Platform"
        assert len(fetched["milestones"]) == 3

    def test_unknown_template_is_not_found(self, client: TestClient) -> None:
        assert client.get("/api/v1/projects/templates/does-not-exist").status_code == 404


class TestTemplateAdmin:
    def test_admin_list_includes_inactive_templates_and_toggle_works(
        self, client: TestClient, db_session: Session, template: ProjectTemplate
    ) -> None:
        inactive = _make_template(db_session, title="Inactive Template", is_active=False)

        listed = client.get("/api/v1/projects/templates/admin").json()
        slugs = {t["slug"] for t in listed}
        assert template.slug in slugs
        assert inactive.slug in slugs
        inactive_entry = next(t for t in listed if t["slug"] == inactive.slug)
        assert inactive_entry["is_active"] is False

        public_slugs = {t["slug"] for t in client.get("/api/v1/projects/templates").json()}
        assert inactive.slug not in public_slugs

        activated = client.patch(f"/api/v1/projects/templates/admin/{inactive.id}", json={"is_active": True})
        assert activated.status_code == 200
        assert activated.json()["is_active"] is True


class TestProjectFromTemplate:
    def test_instantiation_seeds_milestones_in_order(
        self, client: TestClient, template: ProjectTemplate
    ) -> None:
        project = _create_from_template(client, template.slug)
        assert project["template_id"] == template.id
        assert project["status"] == "IN_PROGRESS"
        assert project["objective"] == template.objective
        milestones = project["milestones"]
        assert [m["title"] for m in milestones] == [
            "Understand the Business",
            "Data Discovery",
            "Data Model",
        ]
        assert all(m["is_completed"] is False for m in milestones)

    def test_toggle_milestone_completion(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        milestone_id = project["milestones"][0]["id"]

        completed = client.patch(
            f"/api/v1/projects/{project['id']}/milestones/{milestone_id}", json={"is_completed": True}
        )
        assert completed.status_code == 200
        updated_milestone = next(m for m in completed.json()["milestones"] if m["id"] == milestone_id)
        assert updated_milestone["is_completed"] is True
        assert updated_milestone["completed_at"] is not None

        uncompleted = client.patch(
            f"/api/v1/projects/{project['id']}/milestones/{milestone_id}", json={"is_completed": False}
        )
        reverted = next(m for m in uncompleted.json()["milestones"] if m["id"] == milestone_id)
        assert reverted["is_completed"] is False
        assert reverted["completed_at"] is None


class TestArtifactsAndDatasets:
    def test_add_and_delete_artifact(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        created = client.post(
            f"/api/v1/projects/{project['id']}/artifacts",
            json={
                "artifact_type": "SQL_QUERY",
                "ref_id": "some-query-id",
                "label": "Revenue by channel",
                "snapshot": "SELECT channel, SUM(revenue) FROM orders GROUP BY channel;",
                "notes": "Used for the dashboard",
            },
        )
        assert created.status_code == 201, created.text
        artifact_id = created.json()["id"]

        deleted = client.delete(f"/api/v1/projects/{project['id']}/artifacts/{artifact_id}")
        assert deleted.status_code == 204

    def test_add_and_remove_dataset_with_reason(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        # `orders-sample` is one of the datasets already seeded by app.db.seed
        # (used across this whole test session — see tests/conftest.py's
        # _setup_database fixture, which runs the real seed script).
        added = client.post(
            f"/api/v1/projects/{project['id']}/datasets",
            json={"dataset_id": "orders-sample", "reason": "Needed for the revenue-by-channel analysis"},
        )
        assert added.status_code == 201, added.text
        project_dataset_id = added.json()["id"]
        assert added.json()["reason"] == "Needed for the revenue-by-channel analysis"

        removed = client.delete(f"/api/v1/projects/{project['id']}/datasets/{project_dataset_id}")
        assert removed.status_code == 204

    def test_unknown_dataset_is_not_found(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        response = client.post(
            f"/api/v1/projects/{project['id']}/datasets",
            json={"dataset_id": "not-a-real-dataset", "reason": "x"},
        )
        assert response.status_code == 404


class TestDocumentationPresentationAndLinking:
    def test_update_documentation(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        response = client.patch(
            f"/api/v1/projects/{project['id']}/documentation",
            json={
                "documentation": {
                    "business_problem": "Revenue growth has stalled.",
                    "approach": "Segment by channel and cohort.",
                }
            },
        )
        assert response.status_code == 200
        assert response.json()["documentation"]["business_problem"] == "Revenue growth has stalled."

    def test_update_presentation_slides(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        slides = [
            {"slide": "Business Problem", "content": "Revenue growth has stalled."},
            {"slide": "Executive Summary", "content": "Channel X underperforms."},
        ]
        response = client.patch(
            f"/api/v1/projects/{project['id']}/presentation", json={"presentation": slides}
        )
        assert response.status_code == 200
        assert len(response.json()["presentation"]) == 2

    def test_update_dbt_refs(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        response = client.patch(
            f"/api/v1/projects/{project['id']}/dbt-refs", json={"dbt_model_refs": ["mart_revenue_by_channel"]}
        )
        assert response.status_code == 200
        assert response.json()["dbt_model_refs"] == ["mart_revenue_by_channel"]

    def test_link_and_unlink_data_model(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        linked = client.patch(
            f"/api/v1/projects/{project['id']}/data-model", json={"data_model_id": "some-data-model-id"}
        )
        assert linked.status_code == 200
        assert linked.json()["data_model_id"] == "some-data-model-id"

        unlinked = client.patch(
            f"/api/v1/projects/{project['id']}/data-model", json={"data_model_id": None}
        )
        assert unlinked.json()["data_model_id"] is None


class TestSubmissionAndScoring:
    def test_submit_scores_against_the_template_rubric(
        self, client: TestClient, template: ProjectTemplate
    ) -> None:
        project = _create_from_template(client, template.slug)
        response = client.post(
            f"/api/v1/projects/{project['id']}/submit",
            json={"rubric_selections": {"Business Impact": ["Quantifies revenue impact"]}},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "COMPLETED"
        # Data Quality Awareness 0% * 0.3 + Business Impact 100% * 0.7 = 70
        assert body["score"]["overall"] == 70.0
        assert body["completed_at"] is not None
        assert "what_went_well" in body["score"]["feedback"]

    def test_cannot_submit_twice(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        first = client.post(f"/api/v1/projects/{project['id']}/submit", json={"rubric_selections": {}})
        assert first.status_code == 200
        second = client.post(f"/api/v1/projects/{project['id']}/submit", json={"rubric_selections": {}})
        assert second.status_code >= 400

    def test_free_form_project_cannot_be_submitted_for_rubric_scoring(self, client: TestClient) -> None:
        created = client.post("/api/v1/projects", json={"name": "A free-form project"}).json()
        response = client.post(f"/api/v1/projects/{created['id']}/submit", json={"rubric_selections": {}})
        assert response.status_code >= 400

    def test_reflection_is_saved(self, client: TestClient, template: ProjectTemplate) -> None:
        project = _create_from_template(client, template.slug)
        response = client.patch(
            f"/api/v1/projects/{project['id']}/reflection",
            json={
                "reflection": {
                    "what_learned": "Dimensional modeling end-to-end",
                    "what_difficult": "Handling slowly changing dimensions",
                    "what_differently": "Would prototype the star schema earlier",
                    "skill_improved": "Data modeling",
                    "what_review": "SCD Type 2",
                }
            },
        )
        assert response.status_code == 200
        assert response.json()["reflection"]["skill_improved"] == "Data modeling"


class TestFreeFormProjectRegression:
    """The original Phase 5 shell must keep working unchanged."""

    def test_create_list_get_update_delete(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/projects", json={"name": "Phase 5 shell project", "description": "d"}
        )
        assert created.status_code == 201
        project_id = created.json()["id"]
        assert created.json()["template_id"] is None
        assert created.json()["status"] == "NOT_STARTED"

        listed = client.get("/api/v1/projects").json()
        assert any(p["id"] == project_id for p in listed)

        updated = client.patch(f"/api/v1/projects/{project_id}", json={"status": "IN_PROGRESS"})
        assert updated.json()["status"] == "IN_PROGRESS"

        deleted = client.delete(f"/api/v1/projects/{project_id}")
        assert deleted.status_code == 204
        assert client.get(f"/api/v1/projects/{project_id}").status_code == 404

    def test_create_from_dataset(self, client: TestClient) -> None:
        response = client.post("/api/v1/projects/from-dataset/orders-sample", json={})
        assert response.status_code == 201, response.text
        assert response.json()["dataset_id"] is not None
