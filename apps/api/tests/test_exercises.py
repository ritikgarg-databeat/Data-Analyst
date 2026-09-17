from fastapi.testclient import TestClient


def test_list_exercises(client: TestClient) -> None:
    response = client.get("/api/v1/exercises")

    assert response.status_code == 200
    exercises = response.json()
    assert len(exercises) == 354
    assert any(e["slug"] == "where-vs-having" for e in exercises)


def test_exercise_content_does_not_leak_the_correct_answer(client: TestClient) -> None:
    response = client.get("/api/v1/exercises/select-star-tradeoffs/content")

    assert response.status_code == 200
    body = response.json()
    assert body["exercise_type"] == "MULTIPLE_CHOICE"
    assert len(body["choices"]) == 3
    assert "correct_answer" not in body
    assert "solution" not in body


def test_submitting_a_wrong_multiple_choice_answer_fails_and_updates_mastery(client: TestClient) -> None:
    response = client.post(
        "/api/v1/exercises/select-star-tradeoffs/attempts",
        json={"submitted_answer": "The query fails immediately with a syntax error"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_auto_graded"] is True
    assert body["attempt"]["status"] == "FAILED"
    assert body["attempt"]["score"] == 0.0
    assert body["correct_answer"] is not None  # revealed once graded

    mastery = client.get("/api/v1/skills/mastery").json()
    sql_fundamentals = next(m for m in mastery if m["skill"]["slug"] == "sql-fundamentals")
    assert sql_fundamentals["questions_attempted"] >= 1


def test_submitting_the_correct_answer_passes(client: TestClient) -> None:
    content = client.get("/api/v1/exercises/select-star-tradeoffs/content").json()
    exercise = client.get("/api/v1/exercises/select-star-tradeoffs").json()
    # The correct choice is the one describing a silently-added extra column.
    correct_choice = next(c for c in content["choices"] if "silently gains an extra column" in c)

    response = client.post(
        "/api/v1/exercises/select-star-tradeoffs/attempts", json={"submitted_answer": correct_choice}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["attempt"]["status"] == "PASSED"
    assert body["attempt"]["score"] == 100.0
    assert exercise["exercise_type"] == "MULTIPLE_CHOICE"


def test_hints_reveal_progressively_and_are_tracked(client: TestClient) -> None:
    first = client.post("/api/v1/exercises/where-vs-having/hint")
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["hint_index"] == 0
    assert first_body["hints_remaining"] == 1

    second = client.post("/api/v1/exercises/where-vs-having/hint")
    second_body = second.json()
    assert second_body["hint_index"] == 1
    assert second_body["hints_remaining"] == 0
    assert second_body["hint"] != first_body["hint"]

    # A subsequent submission on this exercise should carry hints_used forward.
    submit = client.post(
        "/api/v1/exercises/where-vs-having/attempts",
        json={"submitted_answer": "WHERE filters rows before grouping, HAVING filters groups after"},
    )
    assert submit.json()["attempt"]["hints_used"] == 2


def test_reveal_solution_marks_attempt_and_returns_explanation(client: TestClient) -> None:
    response = client.post("/api/v1/exercises/monthly-revenue-by-status/solution")

    assert response.status_code == 200
    body = response.json()
    assert body["explanation"]


def test_ungradable_exercise_type_is_recorded_as_submitted(client: TestClient) -> None:
    response = client.post(
        "/api/v1/exercises/top-spending-customers-query/attempts",
        json={"submitted_answer": "SELECT customer_id, SUM(order_total) FROM orders GROUP BY customer_id"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_auto_graded"] is False
    assert body["attempt"]["status"] == "SUBMITTED"


def test_admin_can_reorder_and_deactivate_an_exercise(client: TestClient) -> None:
    exercise = client.get("/api/v1/exercises/where-vs-having").json()

    response = client.patch(f"/api/v1/exercises/{exercise['id']}", json={"display_order": 5})

    assert response.status_code == 200
    assert response.json()["display_order"] == 5
