from fastapi.testclient import TestClient


def test_service_root_identifies_a_healthy_api(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "Data Lab API",
        "status": "ok",
        "health": "/api/v1/health",
        "version": response.json()["version"],
    }


def test_service_root_accepts_platform_head_probe(client: TestClient) -> None:
    response = client.head("/")

    assert response.status_code == 200
    assert response.content == b""


def test_health_returns_ok_status(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "timestamp" in body


def test_database_connection_is_usable(db_session) -> None:  # noqa: ANN001
    from sqlalchemy import text

    result = db_session.execute(text("SELECT 1")).scalar_one()
    assert result == 1
