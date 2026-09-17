from fastapi.testclient import TestClient


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
