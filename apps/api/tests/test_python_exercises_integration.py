"""Integration tests for the real-execution Python exercise grading pipeline
(`/api/v1/python/exercises/{slug}`) against the real
`quarterly-revenue-by-segment` exercise content file, run through
`InProcessKernelBackend` (real kernel execution, no Docker — see
tests/python_lab_fakes.py)."""

from fastapi.testclient import TestClient

CORRECT_CODE = """
payments_success = payments[payments["status"] == "success"].copy()
merged = payments_success.merge(
    orders[["order_id", "customer_id", "order_date"]], on="order_id"
).merge(customers[["customer_id", "customer_segment"]], on="customer_id")
merged["quarter"] = pd.to_datetime(merged["payment_date"]).dt.to_period("Q").astype(str)
result = (
    merged.groupby(["quarter", "customer_segment"])["amount"]
    .sum()
    .round(2)
    .reset_index()
    .rename(columns={"amount": "revenue"})
    .sort_values(["quarter", "revenue"], ascending=[True, False])
    .reset_index(drop=True)
)
"""

WRONG_CODE = """
# forgets to filter to successful payments
merged = payments.merge(
    orders[["order_id", "customer_id"]], on="order_id"
).merge(customers[["customer_id", "customer_segment"]], on="customer_id")
grouped = merged.groupby("customer_segment")["amount"].sum().reset_index()
result = grouped.rename(columns={"amount": "revenue"})
result["quarter"] = "2024Q1"
"""

BROKEN_CODE = "result = payments_that_does_not_exist.sum()"


def test_exercise_content_never_leaks_the_solution_code(client: TestClient) -> None:
    response = client.get("/api/v1/python/exercises/quarterly-revenue-by-segment")
    assert response.status_code == 200
    body = response.json()
    assert body["dataset"] == "ecommerce"
    assert body["result_variable"] == "result"
    assert {f["label"].split(".")[0] for f in body["dataset_files"]} == {"orders", "customers", "payments"}
    assert "python_solution_code" not in body
    assert "solution" not in body
    assert "python_hidden_tests" not in body


def test_rejecting_a_non_python_exercise_slug(client: TestClient) -> None:
    response = client.get("/api/v1/python/exercises/aov-query")  # a SQL exercise
    assert response.status_code == 400


def test_submitting_code_that_fails_to_run_is_graded_zero_with_the_real_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/python/exercises/quarterly-revenue-by-segment/submit", json={"submitted_code": BROKEN_CODE}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["score"] == 0.0
    assert body["passed"] is False
    assert "payments_that_does_not_exist" in body["result"]["error"]["message"]


def test_submitting_code_that_runs_but_is_wrong_fails_with_a_safe_message(client: TestClient) -> None:
    response = client.post(
        "/api/v1/python/exercises/quarterly-revenue-by-segment/submit", json={"submitted_code": WRONG_CODE}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["passed"] is False
    assert body["test_outcomes"][0]["passed"] is False
    assert body["explanation"] is None


def test_submitting_the_correct_code_passes_scores_100_and_reveals_explanation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/python/exercises/quarterly-revenue-by-segment/submit", json={"submitted_code": CORRECT_CODE}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PASSED"
    assert body["score"] == 100.0
    assert body["passed"] is True
    assert body["explanation"]
    outcome_names = [o["name"] for o in body["test_outcomes"]]
    assert "Correct result" in outcome_names
    hidden = [o for o in body["test_outcomes"] if o["is_hidden"]]
    assert len(hidden) == 2
    assert all(o["passed"] for o in hidden)


def test_hidden_tests_are_skipped_when_correctness_fails(client: TestClient) -> None:
    response = client.post(
        "/api/v1/python/exercises/quarterly-revenue-by-segment/submit", json={"submitted_code": WRONG_CODE}
    )
    body = response.json()
    assert len(body["test_outcomes"]) == 1  # only the correctness outcome, no hidden tests ran


def test_a_passed_python_exercise_attempt_is_persisted(client: TestClient) -> None:
    submit = client.post(
        "/api/v1/python/exercises/quarterly-revenue-by-segment/submit", json={"submitted_code": CORRECT_CODE}
    ).json()
    assert submit["attempt_id"]
    assert submit["status"] == "PASSED"
