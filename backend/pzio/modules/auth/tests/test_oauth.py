import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, patch, MagicMock

from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.service import OAuthProviderNotSupportedError, InvalidCredentialsError


def test_oauth_login_google_success_new_user(client: TestClient, db_session: Session) -> None:
    # We will patch oauth.google.get
    with patch("pzio.modules.auth.service.oauth.google.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "email": "new.google@example.com",
            "given_name": "Google",
            "family_name": "User",
        }
        mock_get.return_value = mock_response

        response = client.post(
            "/api/auth/oauth",
            json={"provider": "google", "oauthToken": "fake-google-token"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["tokenType"] == "bearer"
        assert body["expiresIn"] > 0
        assert "accessToken" in body

        # Check DB if user created
        user = db_session.query(User).filter_by(email="new.google@example.com").first()
        assert user is not None
        assert user.first_name == "Google"
        assert user.last_name == "User"


def test_oauth_login_google_success_existing_user(client: TestClient, db_session: Session) -> None:
    # First seed existing user
    user = User(
        email="existing.google@example.com",
        password_hash="some-hash",
        first_name="Old",
        last_name="Name",
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    with patch("pzio.modules.auth.service.oauth.google.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "email": "existing.google@example.com",
            "given_name": "NewGoogle",
            "family_name": "Name",
        }
        mock_get.return_value = mock_response

        response = client.post(
            "/api/auth/oauth",
            json={"provider": "google", "oauthToken": "fake-google-token"},
        )

        assert response.status_code == 200
        assert "accessToken" in response.json()


def test_oauth_login_deactivated_user_returns_403(client: TestClient, db_session: Session) -> None:
    user = User(
        email="blocked.google@example.com",
        password_hash="some-hash",
        first_name="Blocked",
        last_name="User",
        role=UserRole.TEAM_MEMBER,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    with patch("pzio.modules.auth.service.oauth.google.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "email": "blocked.google@example.com",
            "given_name": "Blocked",
            "family_name": "User",
        }
        mock_get.return_value = mock_response

        response = client.post(
            "/api/auth/oauth",
            json={"provider": "google", "oauthToken": "fake-google-token"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Konto zostało dezaktywowane. Skontaktuj się z administratorem."
        )


def test_oauth_login_google_invalid_token(client: TestClient, db_session: Session) -> None:
    with patch("pzio.modules.auth.service.oauth.google.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Invalid token")

        response = client.post(
            "/api/auth/oauth",
            json={"provider": "google", "oauthToken": "invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired OAuth token"


def test_oauth_login_github_success(client: TestClient, db_session: Session) -> None:
    with patch("pzio.modules.auth.service.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("pzio.modules.auth.service.oauth.github.get", new_callable=AsyncMock) as mock_get:

        # Mockhttpx token exchange
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {"access_token": "real-mocked-token"}
        mock_post.return_value = mock_token_resp

        def side_effect(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            if url == "user/emails":
                mock_resp.json.return_value = [{"email": "github@example.com", "primary": True}]
            elif url == "user":
                mock_resp.json.return_value = {"name": "GitHub User"}
            return mock_resp

        mock_get.side_effect = side_effect

        response = client.post(
            "/api/auth/oauth",
            json={"provider": "github", "oauthToken": "fake-github-code"},
        )

        assert response.status_code == 200
        assert "accessToken" in response.json()


def test_oauth_login_github_no_primary_email(client: TestClient, db_session: Session) -> None:
    with patch("pzio.modules.auth.service.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("pzio.modules.auth.service.oauth.github.get", new_callable=AsyncMock) as mock_get:

        # Mock httpx token exchange
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {"access_token": "real-mocked-token"}
        mock_post.return_value = mock_token_resp

        def side_effect(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            if url == "user/emails":
                mock_resp.json.return_value = [{"email": "github@example.com", "primary": False}]
            return mock_resp

        mock_get.side_effect = side_effect

        response = client.post(
            "/api/auth/oauth",
            json={"provider": "github", "oauthToken": "fake-github-code"},
        )

        assert response.status_code == 401


def test_oauth_login_unsupported_provider(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/auth/oauth",
        json={"provider": "facebook", "oauthToken": "fake-token"},
    )

    assert response.status_code == 400
    assert "Unsupported provider" in response.json()["detail"]


def test_oauth_login_github_profile_fail_no_name(client: TestClient, db_session: Session) -> None:
    with patch("pzio.modules.auth.service.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("pzio.modules.auth.service.oauth.github.get", new_callable=AsyncMock) as mock_get:

        # Mock httpx token exchange
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {"access_token": "real-mocked-token"}
        mock_post.return_value = mock_token_resp

        def side_effect(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            if url == "user/emails":
                mock_resp.json.return_value = [{"email": "noname@example.com", "primary": True}]
            elif url == "user":
                mock_resp.raise_for_status.side_effect = Exception("User info failed")
            return mock_resp

        mock_get.side_effect = side_effect

        response = client.post(
            "/api/auth/oauth",
            json={"provider": "github", "oauthToken": "fake-github-code"},
        )

        assert response.status_code == 200
        assert "accessToken" in response.json()