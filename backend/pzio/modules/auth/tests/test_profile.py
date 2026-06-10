from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import create_access_token


def _create_user(db: Session, email="me@example.com") -> User:
    user = User(
        email=email,
        password_hash="hash",
        first_name="Me",
        last_name="User",
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_auth_headers(user: User) -> dict:
    token, _ = create_access_token(user.user_id, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_get_profile_success(client: TestClient, db_session: Session) -> None:
    user = _create_user(db_session)
    headers = _get_auth_headers(user)

    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == user.email
    assert data["firstName"] == user.first_name
    assert data["lastName"] == user.last_name


def test_get_profile_unauthorized(client: TestClient) -> None:
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_update_profile_success(client: TestClient, db_session: Session) -> None:
    user = _create_user(db_session)
    headers = _get_auth_headers(user)

    response = client.patch("/api/users/me", headers=headers, json={"firstName": "NewMe", "lastName": "NewUser"})
    assert response.status_code == 200

    data = response.json()
    assert data["firstName"] == "NewMe"
    assert data["lastName"] == "NewUser"

    # Check DB
    db_session.refresh(user)
    assert user.first_name == "NewMe"
    assert user.last_name == "NewUser"


def test_update_profile_accepts_valid_avatar_url(client: TestClient, db_session: Session) -> None:
    user = _create_user(db_session)
    headers = _get_auth_headers(user)
    avatar_url = "https://cdn.example.com/avatars/42.png"

    response = client.patch("/api/users/me", headers=headers, json={"avatar": avatar_url})
    assert response.status_code == 200
    assert response.json()["avatar"] == avatar_url

    db_session.refresh(user)
    assert user.avatar == avatar_url


def test_update_profile_clears_avatar_when_empty_string(
    client: TestClient, db_session: Session
) -> None:
    user = _create_user(db_session)
    user.avatar = "https://cdn.example.com/avatars/42.png"
    db_session.commit()
    headers = _get_auth_headers(user)

    response = client.patch("/api/users/me", headers=headers, json={"avatar": ""})
    assert response.status_code == 200
    assert response.json()["avatar"] is None

    db_session.refresh(user)
    assert user.avatar is None


def test_update_profile_rejects_non_url_avatar(client: TestClient, db_session: Session) -> None:
    user = _create_user(db_session)
    headers = _get_auth_headers(user)

    response = client.patch("/api/users/me", headers=headers, json={"avatar": "not a url"})
    assert response.status_code == 400


def test_update_profile_rejects_non_http_avatar_scheme(
    client: TestClient, db_session: Session
) -> None:
    user = _create_user(db_session)
    headers = _get_auth_headers(user)

    response = client.patch(
        "/api/users/me", headers=headers, json={"avatar": "ftp://example.com/avatar.png"}
    )
    assert response.status_code == 400
