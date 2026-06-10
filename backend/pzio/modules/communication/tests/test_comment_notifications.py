from fastapi.testclient import TestClient

from pzio.main import app
from pzio.modules.auth.security import create_access_token
from pzio.modules.communication.deps import provide_email_service
from pzio.modules.communication.mock import MockEmailService


def _post_comment(client: TestClient, task_id: int, token: str, content: str = "Looks good to me."):
    return client.post(
        f"/api/tasks/{task_id}/comments",
        json={"content": content},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_first_comment_with_assignee_notifies_assignee_only(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    assignee = user_factory(email="assignee@example.com", first_name="Assign", last_name="Ee")
    author = user_factory(email="author@example.com", first_name="Auth", last_name="Or")
    task = task_factory(title="Deploy hotfix", assignee_id=assignee.user_id)

    mock_email_service = MockEmailService()
    app.dependency_overrides[provide_email_service] = lambda: mock_email_service
    try:
        token, _ = create_access_token(author.user_id, author.role)
        response = _post_comment(client, task.id, token)
    finally:
        app.dependency_overrides.pop(provide_email_service, None)

    assert response.status_code == 201
    assert len(mock_email_service.sent_emails) == 1
    email = mock_email_service.sent_emails[0]
    assert email["to"] == assignee.email
    assert email["subject"] == f"New comment on task #{task.id}: Deploy hotfix"
    assert f"Task ID: {task.id}" in email["body"]
    assert "Task title: Deploy hotfix" in email["body"]
    assert f"Commented by: {author.first_name} {author.last_name} <{author.email}>" in email["body"]


def test_first_comment_without_assignee_sends_no_email(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    author = user_factory(email="solo@example.com")
    task = task_factory(assignee_id=None)

    mock_email_service = MockEmailService()
    app.dependency_overrides[provide_email_service] = lambda: mock_email_service
    try:
        token, _ = create_access_token(author.user_id, author.role)
        response = _post_comment(client, task.id, token)
    finally:
        app.dependency_overrides.pop(provide_email_service, None)

    assert response.status_code == 201
    assert mock_email_service.sent_emails == []


def test_second_comment_notifies_assignee_and_previous_commenter(
    client: TestClient,
    user_factory,
    task_factory,
    comment_factory,
) -> None:
    assignee = user_factory(email="assignee@example.com")
    first_commenter = user_factory(email="first@example.com")
    second_commenter = user_factory(email="second@example.com")
    task = task_factory(title="Review API", assignee_id=assignee.user_id)
    comment_factory(task_id=task.id, author_id=first_commenter.user_id, content="First thought")

    mock_email_service = MockEmailService()
    app.dependency_overrides[provide_email_service] = lambda: mock_email_service
    try:
        token, _ = create_access_token(second_commenter.user_id, second_commenter.role)
        response = _post_comment(client, task.id, token, content="Follow-up")
    finally:
        app.dependency_overrides.pop(provide_email_service, None)

    assert response.status_code == 201
    recipients = {email["to"] for email in mock_email_service.sent_emails}
    assert recipients == {assignee.email, first_commenter.email}
    assert len(mock_email_service.sent_emails) == 2


def test_assignee_commenting_does_not_notify_self(
    client: TestClient,
    user_factory,
    task_factory,
    comment_factory,
) -> None:
    assignee = user_factory(email="assignee@example.com")
    other = user_factory(email="other@example.com")
    task = task_factory(assignee_id=assignee.user_id)
    comment_factory(task_id=task.id, author_id=other.user_id, content="Need update")

    mock_email_service = MockEmailService()
    app.dependency_overrides[provide_email_service] = lambda: mock_email_service
    try:
        token, _ = create_access_token(assignee.user_id, assignee.role)
        response = _post_comment(client, task.id, token, content="On it")
    finally:
        app.dependency_overrides.pop(provide_email_service, None)

    assert response.status_code == 201
    assert len(mock_email_service.sent_emails) == 1
    assert mock_email_service.sent_emails[0]["to"] == other.email


def test_add_comment_unknown_task_returns_404(client: TestClient, user_factory) -> None:
    user = user_factory()
    token, _ = create_access_token(user.user_id, user.role)

    response = _post_comment(client, 99999, token)

    assert response.status_code == 404
