from fastapi.testclient import TestClient


def test_list_skills_returns_all_seeded_skills(client: TestClient) -> None:
    response = client.get("/api/v1/skills")

    assert response.status_code == 200
    skills = response.json()
    assert len(skills) == 38
    categories = {s["category"] for s in skills}
    assert "SQL" in categories
    assert "PYTHON" in categories


def test_get_skill_by_slug(client: TestClient) -> None:
    response = client.get("/api/v1/skills/advanced-sql")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Advanced SQL"
    assert body["category"] == "SQL"
    assert body["target_level"] == "ADVANCED"


def test_skill_mastery_covers_every_skill_with_a_valid_level(client: TestClient) -> None:
    response = client.get("/api/v1/skills/mastery")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 38
    valid_levels = {"BEGINNER", "DEVELOPING", "INTERMEDIATE", "STRONG", "MASTERED"}
    assert all(item["mastery_level"] in valid_levels for item in body)
    assert all(0.0 <= item["mastery_score"] <= 100.0 for item in body)
    # A skill nothing has touched yet must still report a clean zero, not stale data.
    untouched = next(item for item in body if item["skill"]["slug"] == "data-modeling")
    assert untouched["mastery_score"] == 0.0
    assert untouched["mastery_level"] == "BEGINNER"
    assert untouched["questions_attempted"] == 0


def test_admin_can_create_and_update_a_skill(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/skills",
        json={"slug": "temp-skill", "name": "Temp Skill", "category": "SQL", "target_level": "BEGINNER"},
    )
    assert create_response.status_code == 201
    created = create_response.json()

    update_response = client.patch(f"/api/v1/skills/{created['id']}", json={"name": "Renamed Skill"})
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Renamed Skill"
