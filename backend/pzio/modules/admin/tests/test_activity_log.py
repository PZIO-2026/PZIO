from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.modules.admin import service
from pzio.modules.auth.models import UserRole

from ._helpers import auth_header, seed_user


def test_get_history_returns_empty_list_for_unknown_task(
    client: TestClient, db_session: Session
) -> None:
    member = seed_user(db_session, email="member@example.com", role=UserRole.TEAM_MEMBER)

    response = client.get("/api/tasks/999/history", headers=auth_header(member))

    assert response.status_code == 200
    assert response.json() == []


def test_get_history_returns_logged_entries(client: TestClient, db_session: Session) -> None:
    actor = seed_user(db_session, email="manager@example.com", role=UserRole.MANAGER)

    service.log_activity(
        db_session,
        task_id=42,
        user_id=actor.user_id,
        action="status_changed",
        field_name="status",
        old_value="To Do",
        new_value="In Progress",
    )
    service.log_activity(
        db_session,
        task_id=42,
        user_id=actor.user_id,
        action="updated",
        field_name="title",
        old_value="Foo",
        new_value="Bar",
    )

    response = client.get("/api/tasks/42/history", headers=auth_header(actor))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    first = body[0]
    assert first["taskId"] == 42
    assert first["userId"] == actor.user_id
    assert first["action"] == "status_changed"
    assert first["fieldName"] == "status"
    assert first["oldValue"] == "To Do"
    assert first["newValue"] == "In Progress"
    assert "createdAt" in first
    assert "activityLogId" in first


def test_get_history_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/tasks/1/history")
    assert response.status_code == 401
