from fastapi.testclient import TestClient


def _start_attempt(client: TestClient) -> dict:
    response = client.post("/api/v1/assessments/sql-fundamentals-assessment/attempts")
    assert response.status_code == 201
    return response.json()


def test_start_assessment_returns_questions_without_answers(client: TestClient) -> None:
    body = _start_attempt(client)

    assert body["attempt"]["status"] == "IN_PROGRESS"
    assert len(body["questions"]) == 3
    for question in body["questions"]:
        assert "correct_answer" not in question
        assert "solution" not in question


def test_submitting_all_correct_answers_passes(client: TestClient) -> None:
    started = _start_attempt(client)
    attempt_id = started["attempt"]["id"]

    answers = []
    for question in started["questions"]:
        content = client.get(f"/api/v1/exercises/{question['slug']}/content").json()
        if question["exercise_type"] == "MULTIPLE_CHOICE":
            correct = next(c for c in content["choices"] if "silently gains an extra column" in c)
        elif question["exercise_type"] == "TRUE_FALSE":
            correct = "False"
        else:
            correct = "WHERE filters individual rows before grouping; HAVING filters groups after aggregation"
        answers.append({"exercise_id": question["id"], "submitted_answer": correct})

    response = client.post(
        f"/api/v1/assessments/sql-fundamentals-assessment/attempts/{attempt_id}/submit",
        json={"answers": answers, "time_spent_seconds": 300},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["attempt"]["score"] == 100.0
    assert body["attempt"]["status"] == "PASSED"
    assert all(a["is_correct"] for a in body["answers"])


def test_submitting_no_correct_answers_fails(client: TestClient) -> None:
    started = _start_attempt(client)
    attempt_id = started["attempt"]["id"]

    answers = [{"exercise_id": q["id"], "submitted_answer": "definitely wrong"} for q in started["questions"]]

    response = client.post(
        f"/api/v1/assessments/sql-fundamentals-assessment/attempts/{attempt_id}/submit",
        json={"answers": answers, "time_spent_seconds": 60},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert body["attempt"]["score"] == 0.0
    assert body["attempt"]["status"] == "FAILED"


def test_cannot_resubmit_a_completed_attempt(client: TestClient) -> None:
    started = _start_attempt(client)
    attempt_id = started["attempt"]["id"]
    answers = [{"exercise_id": q["id"], "submitted_answer": "x"} for q in started["questions"]]
    client.post(
        f"/api/v1/assessments/sql-fundamentals-assessment/attempts/{attempt_id}/submit",
        json={"answers": answers, "time_spent_seconds": 10},
    )

    response = client.post(
        f"/api/v1/assessments/sql-fundamentals-assessment/attempts/{attempt_id}/submit",
        json={"answers": answers, "time_spent_seconds": 10},
    )

    assert response.status_code == 400


def test_module_without_assessment_returns_404_when_starting(client: TestClient) -> None:
    response = client.post("/api/v1/assessments/does-not-exist/attempts")

    assert response.status_code == 404
