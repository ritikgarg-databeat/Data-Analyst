from fastapi.testclient import TestClient


def test_list_modules_for_domain(client: TestClient) -> None:
    response = client.get("/api/v1/domains/sql/modules")

    assert response.status_code == 200
    modules = response.json()
    assert [m["slug"] for m in modules] == [
        "sql-fundamentals",
        "sql-functions-expressions",
        "sql-aggregation",
        "sql-joins",
        "sql-subqueries-ctes",
        "sql-window-functions",
        "sql-analytical-sql",
        "sql-performance",
        "sql-interview-prep",
    ]
    assert modules[0]["lesson_count"] == 8
    assert modules[2]["lesson_count"] == 7
    assert modules[0]["has_assessment"] is True
    assert modules[2]["has_assessment"] is False


def test_get_module_by_slug(client: TestClient) -> None:
    response = client.get("/api/v1/modules/sql-fundamentals")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "SQL Fundamentals"
    assert body["difficulty"] == "BEGINNER"
    assert body["domain_slug"] == "sql"


def test_modules_for_domain_with_no_modules_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/v1/domains/machine-learning/modules")

    assert response.status_code == 200
    assert response.json() == []


def test_admin_can_create_and_update_a_module(client: TestClient) -> None:
    domain = client.get("/api/v1/domains/sql").json()

    create_response = client.post(
        "/api/v1/modules",
        json={"domain_id": domain["id"], "slug": "temp-module", "title": "Temp Module"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["domain_slug"] == "sql"

    update_response = client.patch(f"/api/v1/modules/{created['id']}", json={"title": "Renamed Module"})
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Renamed Module"


def test_get_module_assessment(client: TestClient) -> None:
    response = client.get("/api/v1/modules/sql-fundamentals/assessment")

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "sql-fundamentals-assessment"
    assert body["question_count"] == 3
    assert body["passing_score"] == 80


def test_module_without_assessment_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/modules/sql-aggregation/assessment")

    assert response.status_code == 404
