from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, NotFoundError
from app.core.security import utc_now
from app.models.dataset import Dataset
from app.models.enums import DatasetSourceType
from app.schemas.project import CreateProjectFromDatasetRequest
from app.services.auth_service import AuthService
from app.services.dataset_service import DatasetService
from app.services.project_service import ProjectService


def _signup(client: TestClient, email: str = "new.user@example.com"):
    return client.post(
        "/api/v1/auth/signup",
        json={"name": "New User", "email": email, "password": "a secure password 123"},
    )


def test_protected_routes_require_authentication(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_signup_normalizes_email_and_disables_ai_by_default(anonymous_client: TestClient) -> None:
    response = _signup(anonymous_client, "  Mixed.Case@Example.com ")
    assert response.status_code == 201, response.text
    assert response.json()["user"]["email"] == "mixed.case@example.com"
    assert response.json()["user"]["ai_access_enabled"] is False
    duplicate = _signup(anonymous_client, "mixed.case@example.com")
    assert duplicate.status_code == 409


def test_csrf_is_required_for_authenticated_mutations(anonymous_client: TestClient) -> None:
    response = _signup(anonymous_client, "csrf.user@example.com")
    assert response.status_code == 201
    denied = anonymous_client.post("/api/v1/auth/logout")
    assert denied.status_code == 403
    csrf = anonymous_client.cookies["dal_csrf_token"]
    allowed = anonymous_client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert allowed.status_code == 200


def test_untrusted_browser_origin_is_rejected(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        "/api/v1/auth/signup",
        headers={"Origin": "https://attacker.example"},
        json={
            "name": "Origin Test",
            "email": "origin.test@example.com",
            "password": "valid-password-123",
        },
    )
    assert response.status_code == 403


def test_login_lockout_after_five_failures(anonymous_client: TestClient) -> None:
    assert _signup(anonymous_client, "locked.user@example.com").status_code == 201
    anonymous_client.cookies.clear()
    for _ in range(5):
        response = anonymous_client.post(
            "/api/v1/auth/login",
            json={"email": "locked.user@example.com", "password": "wrong-password-value"},
        )
        assert response.status_code == 401
    locked = anonymous_client.post(
        "/api/v1/auth/login",
        json={"email": "locked.user@example.com", "password": "a secure password 123"},
    )
    assert locked.status_code == 429


def test_refresh_rotation_rejects_replay(anonymous_client: TestClient) -> None:
    assert _signup(anonymous_client, "refresh.user@example.com").status_code == 201
    old_refresh = anonymous_client.cookies["dal_refresh_token"]
    csrf = anonymous_client.cookies["dal_csrf_token"]
    rotated = anonymous_client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf})
    assert rotated.status_code == 200, rotated.text
    anonymous_client.cookies.set("dal_refresh_token", old_refresh)
    replay_csrf = anonymous_client.cookies["dal_csrf_token"]
    replay = anonymous_client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": replay_csrf})
    assert replay.status_code == 401


def test_two_user_dataset_isolation(db_session: Session) -> None:
    first = AuthService(db_session).signup("First", "first.isolation@example.com", "first password 1234")
    second = AuthService(db_session).signup("Second", "second.isolation@example.com", "second password 123")
    private = Dataset(
        owner_user_id=first.id,
        name="Private",
        slug="private-isolation-test",
        source_type=DatasetSourceType.LOCAL,
    )
    db_session.add(private)
    db_session.commit()
    assert DatasetService(db_session, user_id=first.id).get(private.id).id == private.id
    try:
        DatasetService(db_session, user_id=second.id).get(private.id)
    except NotFoundError:
        pass
    else:
        raise AssertionError("Another user's private dataset was visible")


def test_admin_cannot_suspend_self(client: TestClient) -> None:
    current = client.get("/api/v1/users/me").json()
    response = client.post(f"/api/v1/admin/users/{current['id']}/suspend")
    assert response.status_code == 403


def test_shared_datasets_are_read_only_for_learners(client: TestClient) -> None:
    response = client.post("/api/v1/datasets/orders-sample/profile")
    assert response.status_code == 404


def test_project_dataset_lookup_hides_another_users_private_dataset(db_session: Session) -> None:
    first = AuthService(db_session).signup("Owner", "project.owner@example.com", "project owner password")
    second = AuthService(db_session).signup("Other", "project.other@example.com", "project other password")
    private = Dataset(
        owner_user_id=first.id,
        name="Project private",
        slug="project-private-isolation",
        source_type=DatasetSourceType.LOCAL,
    )
    db_session.add(private)
    db_session.commit()
    with pytest.raises(NotFoundError):
        ProjectService(db_session).create_from_dataset(
            second.id, private.id, CreateProjectFromDatasetRequest()
        )


def test_admin_reset_is_one_time_response_and_expired_password_is_rejected(
    client: TestClient, db_session: Session
) -> None:
    target = AuthService(db_session).signup(
        "Reset Target", "reset.target@example.com", "original password 123"
    )
    response = client.post(
        f"/api/v1/admin/users/{target.id}/reset-password",
        json={"current_password": "test-password-123"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    temporary = response.json()["temporary_password"]
    db_session.refresh(target)
    assert target.must_change_password is True
    target.temporary_password_expires_at = utc_now() - timedelta(seconds=1)
    db_session.commit()
    with pytest.raises(AuthenticationError):
        AuthService(db_session).authenticate(target.email, temporary)


def test_admin_read_sections_never_serialize_passwords_or_tokens(client: TestClient) -> None:
    current = client.get("/api/v1/users/me").json()
    for section in ("learning", "labs", "projects", "datasets", "career", "interviews", "ai"):
        response = client.get(f"/api/v1/admin/users/{current['id']}/data/{section}")
        assert response.status_code == 200, response.text
        assert "password_hash" not in response.text
        assert "refresh_token_hash" not in response.text
