from fastapi.testclient import TestClient


def test_search_finds_lessons_modules_and_exercises_by_keyword(client: TestClient) -> None:
    response = client.get("/api/v1/search", params={"q": "having"})

    assert response.status_code == 200
    body = response.json()
    kinds = {r["kind"] for r in body["results"]}
    slugs = {r["slug"] for r in body["results"]}
    assert "lesson" in kinds
    assert "having" in slugs
    assert "where-vs-having" in slugs


def test_search_can_be_filtered_by_kind(client: TestClient) -> None:
    response = client.get("/api/v1/search", params={"q": "sql", "kind": "skill"})

    assert response.status_code == 200
    body = response.json()
    assert all(r["kind"] == "skill" for r in body["results"])


def test_empty_query_returns_no_results(client: TestClient) -> None:
    response = client.get("/api/v1/search", params={"q": ""})

    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_covers_cases_projects_interview_questions_and_metrics(client: TestClient) -> None:
    """Phase 12 extension — search originally covered only domain/module/
    lesson/skill/exercise; a platform audit found cases/projects/interview
    questions/metrics were invisible to global search despite existing."""
    for kind in ("case", "project", "interview_question", "metric"):
        response = client.get("/api/v1/search", params={"q": "revenue", "kind": kind})
        assert response.status_code == 200
        assert all(r["kind"] == kind for r in response.json()["results"])

