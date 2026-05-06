from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.main import app
from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import create_access_token, hash_password
from pzio.modules.communication.deps import provide_email_service
from pzio.modules.communication.mock import MockEmailService


def _seed_user(
    db: Session,
    *,
    email: str = "commenter@example.com",
    password: str = "s3cret-pass",
    first_name: str = "Ada",
    last_name: str = "Lovelace",
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_add_comment_sends_email_notification(client: TestClient, db_session: Session) -> None:
    user = _seed_user(db_session)
    token, _ = create_access_token(user.user_id, user.role)

    mock_email_service = MockEmailService()
    app.dependency_overrides[provide_email_service] = lambda: mock_email_service
    try:
        response = client.post(
            "/api/tasks/123/comments",
            json={"content": "Looks good to me."},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(provide_email_service, None)

    assert response.status_code == 201
    assert len(mock_email_service.sent_emails) == 1

    email = mock_email_service.sent_emails[0]
    assert email["to"] == user.email
    assert email["subject"] == "New comment on task #123"
    assert "Task ID: 123" in email["body"]
    assert f"Commented by: {user.first_name} {user.last_name} <{user.email}>" in email["body"]
    assert "Looks good to me." in email["body"]
