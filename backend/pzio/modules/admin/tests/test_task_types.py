from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.modules.admin.models import TaskType
from pzio.modules.auth.models import UserRole

from ._helpers import auth_header, seed_user


def test_add_task_type_as_admin_returns_201(client: TestClient, db_session: Session) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)

    response = client.post(
        "/api/admin/task-types",
        json={"name": "Spike"},
        headers=auth_header(admin),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Spike"
    assert isinstance(body["taskTypeId"], int)
    assert "createdAt" in body

    # Persisted row matches what we returned.
    stored = db_session.get(TaskType, body["taskTypeId"])
    assert stored is not None
    assert stored.name == "Spike"


def test_add_task_type_rejects_duplicate_name_with_409(
    client: TestClient, db_session: Session
) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    headers = auth_header(admin)

    first = client.post("/api/admin/task-types", json={"name": "Spike"}, headers=headers)
    assert first.status_code == 201

    second = client.post("/api/admin/task-types", json={"name": "Spike"}, headers=headers)
    assert second.status_code == 409
    assert isinstance(second.json()["detail"], str)


def test_add_task_type_as_non_admin_returns_403(client: TestClient, db_session: Session) -> None:
    member = seed_user(db_session, email="member@example.com", role=UserRole.TEAM_MEMBER)

    response = client.post(
        "/api/admin/task-types",
        json={"name": "Spike"},
        headers=auth_header(member),
    )

    assert response.status_code == 403


def test_add_task_type_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/api/admin/task-types", json={"name": "Spike"})
    assert response.status_code == 401


def test_add_task_type_rejects_empty_name_with_400(client: TestClient, db_session: Session) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)

    response = client.post(
        "/api/admin/task-types",
        json={"name": "   "},
        headers=auth_header(admin),
    )

    # str_strip_whitespace + min_length=1 → trimmed empty string fails validation.
    assert response.status_code == 400


def test_get_task_types_returns_inserted_items(client: TestClient, db_session: Session) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    headers = auth_header(admin)

    client.post("/api/admin/task-types", json={"name": "Spike"}, headers=headers)
    client.post("/api/admin/task-types", json={"name": "Bug"}, headers=headers)

    response = client.get("/api/task-types", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    names = [item["name"] for item in body]
    assert names == ["Spike", "Bug"]


def test_get_task_types_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/task-types")
    assert response.status_code == 401
