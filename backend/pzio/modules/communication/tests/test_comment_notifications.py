from fastapi.testclient import TestClient

from pzio.main import app
from pzio.modules.auth.security import create_access_token
from pzio.modules.communication.deps import provide_email_service
from pzio.modules.communication.mock import MockEmailService


def test_add_comment_sends_email_notification(client: TestClient, user_factory) -> None:
    user = user_factory(email="commenter@example.com")
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
