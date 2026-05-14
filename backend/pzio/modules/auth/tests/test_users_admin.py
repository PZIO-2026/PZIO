from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import create_access_token


def _create_user(db: Session, email="test@example.com", role=UserRole.TEAM_MEMBER, is_active=True) -> User:
    user = User(
        email=email,
        password_hash="hash",
        first_name="Test",
        last_name="User",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_auth_headers(user: User) -> dict:
    token, _ = create_access_token(user.user_id, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_list_users_as_admin_success(client: TestClient, db_session: Session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    target_user = _create_user(db_session, email="target@example.com")

    headers = _get_auth_headers(admin)

    response = client.get("/api/users?size=10&page=1&sortDirection=asc&sortBy=email", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 2
    assert "items" in data

    emails = [i["email"] for i in data["items"]]
    assert admin.email in emails
    assert target_user.email in emails


def test_list_users_search_filter(client: TestClient, db_session: Session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    target = _create_user(db_session, email="unique.search@example.com")
    _create_user(db_session, email="another@example.com")

    headers = _get_auth_headers(admin)

    response = client.get("/api/users?search=unique", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "unique.search@example.com"


def test_list_users_active_filter(client: TestClient, db_session: Session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    _create_user(db_session, email="inactive@example.com", is_active=False)

    headers = _get_auth_headers(admin)

    response = client.get("/api/users?isActive=false", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "inactive@example.com"


def test_list_users_as_member_returns_403(client: TestClient, db_session: Session) -> None:
    member = _create_user(db_session)
    headers = _get_auth_headers(member)

    response = client.get("/api/users", headers=headers)
    assert response.status_code == 403


def test_update_user_status_as_admin_success(client: TestClient, db_session: Session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    target = _create_user(db_session, email="target@example.com", is_active=True)

    headers = _get_auth_headers(admin)

    response = client.patch(f"/api/users/{target.user_id}/status", json={"isActive": False}, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["isActive"] is False

    # Check DB
    db_session.refresh(target)
    assert target.is_active is False


def test_update_user_status_not_found(client: TestClient, db_session: Session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    headers = _get_auth_headers(admin)

    response = client.patch("/api/users/99999/status", json={"isActive": False}, headers=headers)
    assert response.status_code == 404


def test_list_users_no_sort(client: TestClient, db_session: Session) -> None:
    admin = _create_user(db_session, email="admin2@example.com", role=UserRole.ADMINISTRATOR)
    headers = _get_auth_headers(admin)
    response = client.get("/api/users", headers=headers)
    assert response.status_code == 200
