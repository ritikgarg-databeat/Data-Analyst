from fastapi.testclient import TestClient


def test_list_lessons_for_module(client: TestClient) -> None:
    response = client.get("/api/v1/modules/sql-fundamentals/lessons")

    assert response.status_code == 200
    lessons = response.json()
    assert [lesson["slug"] for lesson in lessons] == [
        "select",
        "where",
        "order-by",
        "limit",
        "distinct",
        "null-handling",
        "case-expressions",
        "basic-functions",
    ]


def test_get_lesson_by_slug_includes_content_reference(client: TestClient) -> None:
    response = client.get("/api/v1/lessons/select")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "SELECT"
    assert body["content_reference"] == "content/lessons/sql/sql-fundamentals/select.yaml"
    assert body["module_slug"] == "sql-fundamentals"
    assert body["domain_slug"] == "sql"
    assert any(tag["slug"] == "sql" for tag in body["tags"])
    assert any(skill["slug"] == "sql-fundamentals" for skill in body["skills"])


def test_get_unknown_lesson_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/lessons/does-not-exist")

    assert response.status_code == 404


def test_lesson_content_renders_blocks_from_content_file(client: TestClient) -> None:
    response = client.get("/api/v1/lessons/select/content")

    assert response.status_code == 200
    body = response.json()
    assert len(body["blocks"]) >= 5
    assert len(body["objectives"]) >= 1
    assert len(body["key_takeaways"]) >= 1
    assert any(block["type"] == "question" for block in body["blocks"])
    assert body["progress"]["status"] == "NOT_STARTED"
    assert body["is_locked"] is False
    assert body["next_lesson"]["slug"] == "where"
    assert body["previous_lesson"] is None


def test_second_lesson_in_module_has_a_hard_prerequisite(client: TestClient) -> None:
    response = client.get("/api/v1/lessons/where/content")

    assert response.status_code == 200
    body = response.json()
    assert body["is_locked"] is True
    assert len(body["prerequisites"]) == 1
    prereq = body["prerequisites"][0]
    assert prereq["lesson"]["slug"] == "select"
    assert prereq["is_hard_blocker"] is True
    assert prereq["is_completed"] is False


def test_admin_can_reorder_and_deactivate_a_lesson(client: TestClient) -> None:
    lesson = client.get("/api/v1/lessons/mean").json()

    response = client.patch(f"/api/v1/lessons/{lesson['id']}", json={"is_active": False, "display_order": 99})

    assert response.status_code == 200
    body = response.json()
    assert body["is_active"] is False
    assert body["display_order"] == 99

    # Restore so later/other test runs aren't affected.
    client.patch(
        f"/api/v1/lessons/{lesson['id']}", json={"is_active": True, "display_order": lesson["display_order"]}
    )
