from fastapi.testclient import TestClient


def test_list_tags_returns_seeded_tags(client: TestClient) -> None:
    response = client.get("/api/v1/tags")

    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()}
    assert {"sql", "python", "beginner", "interview"}.issubset(slugs)


def test_create_update_and_delete_a_tag(client: TestClient) -> None:
    create_response = client.post("/api/v1/tags", json={"slug": "temp-tag", "name": "Temp Tag"})
    assert create_response.status_code == 201
    tag = create_response.json()

    update_response = client.patch(f"/api/v1/tags/{tag['id']}", json={"name": "Renamed Tag"})
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Renamed Tag"

    delete_response = client.delete(f"/api/v1/tags/{tag['id']}")
    assert delete_response.status_code == 204

    assert not any(t["id"] == tag["id"] for t in client.get("/api/v1/tags").json())
