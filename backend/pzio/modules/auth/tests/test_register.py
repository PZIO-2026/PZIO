from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import verify_password


VALID_PAYLOAD = {
    "email": "ada@example.com",
    "password": "s3cret-pass",
    "firstName": "Ada",
    "lastName": "Lovelace",
}


def test_register_creates_user_and_returns_201(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/auth/register", json=VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == VALID_PAYLOAD["email"]
    assert body["firstName"] == VALID_PAYLOAD["firstName"]
    assert body["lastName"] == VALID_PAYLOAD["lastName"]
    assert body["role"] == UserRole.TEAM_MEMBER.value
    assert body["isActive"] is True
    assert "userId" in body
    assert "createdAt" in body

    user = db_session.execute(select(User).where(User.email == VALID_PAYLOAD["email"])).scalar_one()
    assert user.role == UserRole.TEAM_MEMBER
    assert user.is_active is True
    assert verify_password(VALID_PAYLOAD["password"], user.password_hash) is True


def test_register_response_never_includes_password_or_hash(client: TestClient) -> None:
    response = client.post("/api/auth/register", json=VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert "password" not in body
    assert "passwordHash" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email_with_409(client: TestClient) -> None:
    first = client.post("/api/auth/register", json=VALID_PAYLOAD)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=VALID_PAYLOAD)
    assert second.status_code == 409
    body = second.json()
    assert isinstance(body["detail"], str)
    assert "email" in body["detail"].lower()


def test_register_rejects_invalid_email_with_400(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


def test_register_rejects_short_password_with_400(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "password": "short"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


def test_register_rejects_missing_field_with_400(client: TestClient) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "lastName"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)
