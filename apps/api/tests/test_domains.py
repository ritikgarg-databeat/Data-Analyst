from fastapi.testclient import TestClient


def test_list_domains_returns_seeded_domains_in_order(client: TestClient) -> None:
    response = client.get("/api/v1/domains")

    assert response.status_code == 200
    domains = response.json()
    assert len(domains) == 17
    slugs = [d["slug"] for d in domains]
    assert slugs[0] == "data-analyst-foundations"
    assert "sql" in slugs
    # display_order should be non-decreasing across the list
    orders = [d["display_order"] for d in domains]
    assert orders == sorted(orders)


def test_get_domain_by_slug(client: TestClient) -> None:
    response = client.get("/api/v1/domains/sql")

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "sql"
    assert body["name"] == "SQL"
    assert body["module_count"] == 9
    assert body["progress_percent"] == 0.0


def test_get_unknown_domain_returns_404_with_structured_error(client: TestClient) -> None:
    response = client.get("/api/v1/domains/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "does-not-exist" in body["error"]["message"]


def test_admin_can_create_and_update_a_domain(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/domains", json={"slug": "temp-domain", "name": "Temp Domain", "display_order": 99}
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["slug"] == "temp-domain"
    assert created["is_active"] is True

    update_response = client.patch(f"/api/v1/domains/{created['id']}", json={"is_active": False})
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False


def test_admin_cannot_create_duplicate_domain_slug(client: TestClient) -> None:
    response = client.post("/api/v1/domains", json={"slug": "sql", "name": "Duplicate SQL"})

    assert response.status_code == 409
