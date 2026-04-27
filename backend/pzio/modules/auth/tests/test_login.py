from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import decode_access_token, hash_password


def _seed_user(
    db: Session,
    *,
    email: str = "ada@example.com",
    password: str = "s3cret-pass",
    is_active: bool = True,
    role: UserRole = UserRole.TEAM_MEMBER,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name="Ada",
        last_name="Lovelace",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_with_valid_credentials_returns_token(client: TestClient, db_session: Session) -> None:
    user = _seed_user(db_session)

    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "s3cret-pass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert body["expiresIn"] > 0
    assert isinstance(body["accessToken"], str) and body["accessToken"]

    claims = decode_access_token(body["accessToken"])
    assert claims["sub"] == str(user.user_id)
    assert claims["role"] == UserRole.TEAM_MEMBER.value


def test_login_with_wrong_password_returns_401(client: TestClient, db_session: Session) -> None:
    user = _seed_user(db_session)

    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "totally-wrong"},
    )

    assert response.status_code == 401
    assert isinstance(response.json()["detail"], str)


def test_login_with_unknown_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "whatever"},
    )

    assert response.status_code == 401


def test_login_for_inactive_user_returns_401(client: TestClient, db_session: Session) -> None:
    user = _seed_user(db_session, is_active=False)

    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "s3cret-pass"},
    )

    assert response.status_code == 401


def test_login_rejects_invalid_email_format_with_400(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": "whatever"},
    )

    assert response.status_code == 400
