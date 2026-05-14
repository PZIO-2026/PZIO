from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from pytest import MonkeyPatch

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import hash_password, create_reset_token
from pzio.modules.communication.base import EmailService
from pzio.modules.communication.deps import provide_email_service


def _seed_user(db: Session, email: str = "reset@example.com") -> User:
    user = User(
        email=email,
        password_hash=hash_password("old-pass"),
        first_name="Reset",
        last_name="User",
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_request_password_reset_sends_email(client: TestClient, db_session: Session) -> None:
    user = _seed_user(db_session)
    mock_email_service = MagicMock(spec=EmailService)

    client.app.dependency_overrides[provide_email_service] = lambda: mock_email_service

    try:
        response = client.post(
            "/api/auth/reset-password",
            json={"email": user.email},
        )
        assert response.status_code == 200
        assert "message" in response.json()

        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args[1]
        assert call_args["to"] == user.email
        assert "Resetowanie has" in call_args["subject"]
    finally:
        client.app.dependency_overrides.pop(provide_email_service, None)


def test_request_password_reset_unknown_email_returns_200_does_not_send(
    client: TestClient, db_session: Session
) -> None:
    mock_email_service = MagicMock(spec=EmailService)
    client.app.dependency_overrides[provide_email_service] = lambda: mock_email_service

    try:
        response = client.post(
            "/api/auth/reset-password",
            json={"email": "unknown@example.com"},
        )
        assert response.status_code == 200
        assert "message" in response.json()

        mock_email_service.send_email.assert_not_called()
    finally:
        client.app.dependency_overrides.pop(provide_email_service, None)


def test_confirm_password_reset_success(client: TestClient, db_session: Session) -> None:
    user = _seed_user(db_session)
    token = create_reset_token(user.email)

    response = client.post(
        "/api/auth/reset-password/confirm",
        json={"token": token, "newPassword": "new-strong-pass"},
    )

    assert response.status_code == 200
    assert "message" in response.json()

    # check if user password actually changed
    # Need to verify via login endpoint to ensure it was properly hashed
    response_login = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "new-strong-pass"},
    )
    assert response_login.status_code == 200


def test_confirm_password_reset_invalid_token(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/auth/reset-password/confirm",
        json={"token": "invalid-token", "newPassword": "new-strong-pass"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


def test_confirm_password_reset_user_deleted(client: TestClient, db_session: Session) -> None:
    # generate token for email that does not exist in DB
    token = create_reset_token("deleted@example.com")

    response = client.post(
        "/api/auth/reset-password/confirm",
        json={"token": token, "newPassword": "new-strong-pass"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
