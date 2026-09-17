from fastapi.testclient import TestClient


def test_progress_summary_before_any_lesson_progress_exists(client: TestClient) -> None:
    # Runs after test_assessments.py/test_exercises.py/test_analytics_cases.py
    # (among others), which already exercise skill mastery via real,
    # dynamically-picked content — so this only asserts what's true regardless
    # of that: no LessonProgress rows have been touched yet at this point in
    # the suite. (Skill mastery correctness itself is covered by test_skills.py,
    # not here — asserting a specific category stays untouched is inherently
    # fragile against unrelated tests that pick content dynamically.)
    response = client.get("/api/v1/progress/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_skills"] == 38
    assert body["continue_learning"] == []
    assert body["recently_completed"] == []
    assert len(body["activity"]) == 14
    assert len(body["skill_overview"]) > 0


def test_upsert_lesson_progress_then_appears_in_summary(client: TestClient) -> None:
    lesson = client.get("/api/v1/lessons/order-by").json()

    upsert_response = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}",
        json={"status": "IN_PROGRESS", "progress_percent": 40},
    )
    assert upsert_response.status_code == 200
    progress = upsert_response.json()
    assert progress["status"] == "IN_PROGRESS"
    assert progress["progress_percent"] == 40
    assert progress["started_at"] is not None

    list_response = client.get("/api/v1/progress/lessons")
    assert any(p["lesson_id"] == lesson["id"] for p in list_response.json())

    summary_response = client.get("/api/v1/progress/summary")
    summary = summary_response.json()
    assert any(item["lesson"]["slug"] == "order-by" for item in summary["continue_learning"])


def test_upsert_progress_for_unknown_lesson_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/progress/lessons/does-not-exist",
        json={"status": "IN_PROGRESS", "progress_percent": 10},
    )
    assert response.status_code == 404


def test_completion_is_not_granted_below_the_reading_threshold(client: TestClient) -> None:
    lesson = client.get("/api/v1/lessons/limit").json()

    response = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}",
        json={"status": "COMPLETED", "progress_percent": 50},
    )

    assert response.status_code == 200
    body = response.json()
    # The default completion rule requires >=90% read — the server must not
    # honor a client-requested COMPLETED status below that.
    assert body["status"] == "IN_PROGRESS"
    assert body["completed_at"] is None


def test_completion_is_granted_at_or_above_the_reading_threshold(client: TestClient) -> None:
    lesson = client.get("/api/v1/lessons/limit").json()

    response = client.post(
        f"/api/v1/progress/lessons/{lesson['id']}",
        json={"status": "COMPLETED", "progress_percent": 95},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None

    summary = client.get("/api/v1/progress/summary").json()
    assert any(item["lesson"]["slug"] == "limit" for item in summary["recently_completed"])


def test_update_lesson_position_tracks_time_and_flips_to_in_progress(client: TestClient) -> None:
    lesson_slug = "distinct"

    response = client.post(
        f"/api/v1/lessons/{lesson_slug}/position",
        json={"last_position": "block-2", "time_spent_delta_seconds": 30},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IN_PROGRESS"
    assert body["last_position"] == "block-2"
    assert body["time_spent_seconds"] == 30

    second_response = client.post(
        f"/api/v1/lessons/{lesson_slug}/position",
        json={"time_spent_delta_seconds": 15},
    )
    assert second_response.json()["time_spent_seconds"] == 45
