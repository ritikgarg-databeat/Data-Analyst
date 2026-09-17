"""Integration tests for the real-execution SQL exercise grading pipeline
(`/api/v1/sql/exercises/{slug}`), as distinct from unit tests of the pure
evaluation math in test_sql_evaluation.py. These exercise the full path:
content loading -> DuckDB execution against the real ecommerce CSVs ->
result-based comparison -> hidden tests -> scoring -> ExerciseAttempt
persistence -> mastery/lesson-progress side effects."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.exercise_attempt import ExerciseAttempt


def test_sql_exercise_content_never_leaks_the_solution_query(client: TestClient) -> None:
    response = client.get("/api/v1/sql/exercises/aov-query")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset"] == "ecommerce"
    assert any(t["table_name"] == "payments" for t in body["tables"])
    assert "sql_solution_query" not in body
    assert "solution" not in body
    assert "sql_hidden_tests" not in body


def test_rejecting_a_non_sql_exercise_slug(client: TestClient) -> None:
    response = client.get("/api/v1/sql/exercises/select-star-tradeoffs")  # a MULTIPLE_CHOICE exercise

    assert response.status_code == 400


def test_submitting_a_query_that_fails_to_execute_is_graded_zero_with_the_real_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/sql/exercises/aov-query/submit",
        json={"submitted_query": "SELECT ROUND(AVG(amnt), 2) FROM payments"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["score"] == 0.0
    assert body["passed"] is False
    assert "amnt" in body["result"]["error"]["message"]  # real DuckDB column-not-found error, not fabricated


def test_submitting_a_query_that_runs_but_is_wrong_fails_with_a_safe_diff_message(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sql/exercises/aov-query/submit",
        json={"submitted_query": "SELECT ROUND(AVG(amount), 2) FROM payments"},  # missing the status filter
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["passed"] is False
    assert body["test_outcomes"][0]["passed"] is False
    assert body["explanation"] is None  # never revealed on failure


def test_submitting_the_correct_query_passes_scores_100_and_reveals_the_explanation(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/sql/exercises/aov-query/submit",
        json={
            "submitted_query": "SELECT ROUND(AVG(amount), 2) AS aov FROM payments WHERE status = 'success'"
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PASSED"
    assert body["score"] == 100.0
    assert body["passed"] is True
    assert body["explanation"]


def test_hidden_tests_run_only_after_correctness_passes_and_are_reported_separately(
    client: TestClient,
) -> None:
    correct_query = (
        "SELECT o.customer_id, ROUND(SUM(p.amount), 2) AS total_spend "
        "FROM orders o JOIN payments p ON p.order_id = o.order_id "
        "WHERE o.status = 'completed' GROUP BY o.customer_id ORDER BY total_spend DESC"
    )
    response = client.post(
        "/api/v1/sql/exercises/top-spending-customers-query/submit", json={"submitted_query": correct_query}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PASSED"
    assert body["score"] == 100.0
    outcome_names = [o["name"] for o in body["test_outcomes"]]
    assert "Correct results" in outcome_names
    hidden = next(o for o in body["test_outcomes"] if o["is_hidden"])
    assert hidden["passed"] is True


def test_a_passed_sql_exercise_attempt_is_persisted_and_retrievable(
    client: TestClient, db_session: Session
) -> None:
    submit = client.post(
        "/api/v1/sql/exercises/aov-query/submit",
        json={
            "submitted_query": "SELECT ROUND(AVG(amount), 2) AS aov FROM payments WHERE status = 'success'"
        },
    ).json()

    attempt = db_session.get(ExerciseAttempt, submit["attempt_id"])

    assert attempt is not None
    assert attempt.status == "PASSED"
    assert attempt.score == 100.0
    assert (
        attempt.submitted_answer
        == "SELECT ROUND(AVG(amount), 2) AS aov FROM payments WHERE status = 'success'"
    )
