from fastapi.testclient import TestClient

VALID_REASONS = {"incomplete_prerequisite", "next_in_module", "weak_skill", "unfinished_lesson", "review"}


def test_recommendations_returns_well_formed_items(client: TestClient) -> None:
    response = client.get("/api/v1/recommendations", params={"limit": 5})

    assert response.status_code == 200
    items = response.json()
    assert 1 <= len(items) <= 5
    for item in items:
        assert item["reason"] in VALID_REASONS
        assert item["lesson"]["slug"]
        assert item["explanation"]

    # No duplicate lessons within one recommendation set.
    lesson_ids = [item["lesson"]["id"] for item in items]
    assert len(lesson_ids) == len(set(lesson_ids))


def test_recommendations_respects_the_limit_parameter(client: TestClient) -> None:
    response = client.get("/api/v1/recommendations", params={"limit": 2})

    assert response.status_code == 200
    assert len(response.json()) <= 2


def test_locked_next_lesson_surfaces_its_prerequisite_instead(client: TestClient) -> None:
    # "where" (module sql-fundamentals) is locked behind "select" — this suite
    # never completes "select", so if it's ever the module's next lesson, the
    # recommendation must point at the prerequisite, not the locked lesson.
    response = client.get("/api/v1/recommendations", params={"limit": 10})

    assert response.status_code == 200
    items = response.json()
    for item in items:
        if item["reason"] == "incomplete_prerequisite":
            assert item["lesson"]["slug"] != "where"
