from collections.abc import Mapping
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.main import app
from pzio.modules.auth.deps import get_current_user
from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import hash_password
import pzio.modules.tasks.models as models


@pytest.fixture(autouse=True)
def override_current_user(db_session: Session) -> None:
    def _override_get_current_user() -> User:
        user = (
            db_session.query(User)
            .filter(User.email == "tasks-test-user@example.com")
            .first()
        )
        if user is None:
            user = User(
                email="tasks-test-user@example.com",
                password_hash=hash_password("irrelevant"),
                first_name="Tasks",
                last_name="Tester",
                role=UserRole.TEAM_MEMBER,
                is_active=True,
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        return user

    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


# --- TESTY ENDPOINTÓW ---


def test_create_task(client: TestClient):
    """Test tworzenia nowego zadania w projekcie (UC5)."""
    payload: Mapping[str, str | int] = {
        "title": "Zaimplementować logowanie",
        "type": "Task",
        "priority": "High",
        "storyPoints": 5,
    }
    response = client.post("/api/projects/1/tasks", json=payload)

    assert response.status_code == 201
    data = cast(dict[str, object], response.json())
    assert data["title"] == payload["title"]
    assert data["type"] == payload["type"]
    assert data["status"] == "ToDo"  # Domyślny status
    assert "id" in data
    assert data["projectId"] == 1


def test_get_tasks(client: TestClient):
    """Test pobierania listy zadań w projekcie z filtrowaniem."""
    # Tworzymy zadania o różnych kombinacjach pól filtrowania
    create_response_1 = client.post(
        "/api/projects/1/tasks",
        json={
            "title": "Task 1",
            "type": "Bug",
            "priority": "Low",
            "status": "Todo",
            "assigneeId": 10,
            "sprintId": 100,
        },
    )
    assert create_response_1.status_code == 201

    create_response_2 = client.post(
        "/api/projects/1/tasks",
        json={
            "title": "Task 2",
            "type": "Task",
            "priority": "High",
            "status": "In Progress",
            "assigneeId": 20,
            "sprintId": 200,
        },
    )
    assert create_response_2.status_code == 201

    create_response_3 = client.post(
        "/api/projects/1/tasks",
        json={
            "title": "Task 3",
            "type": "Bug",
            "priority": "Medium",
            "status": "Todo",
            "assigneeId": 10,
            "sprintId": 200,
        },
    )
    assert create_response_3.status_code == 201

    # Pobieramy wszystko z projektu 1
    response = client.get("/api/projects/1/tasks")
    assert response.status_code == 200
    tasks = cast(list[dict[str, object]], response.json())
    assert len(tasks) == 3

    # Pobieramy z filtrowaniem po typie
    response_filtered = client.get("/api/projects/1/tasks?type=Bug")
    assert response_filtered.status_code == 200
    filtered_tasks = cast(list[dict[str, object]], response_filtered.json())
    assert len(filtered_tasks) == 2
    assert {cast(str, task["title"]) for task in filtered_tasks} == {"Task 1", "Task 3"}

    # Pobieramy z filtrowaniem po statusie
    response_status_filtered = client.get("/api/projects/1/tasks?status=Todo")
    assert response_status_filtered.status_code == 200
    status_filtered_tasks = cast(list[dict[str, object]], response_status_filtered.json())
    assert len(status_filtered_tasks) == 2
    assert {cast(str, task["title"]) for task in status_filtered_tasks} == {"Task 1", "Task 3"}

    # Pobieramy z filtrowaniem po assigneeId
    response_assignee_filtered = client.get("/api/projects/1/tasks?assigneeId=20")
    assert response_assignee_filtered.status_code == 200
    assignee_filtered_tasks = cast(
        list[dict[str, object]], response_assignee_filtered.json()
    )
    assert len(assignee_filtered_tasks) == 1
    assert assignee_filtered_tasks[0]["title"] == "Task 2"

    # Pobieramy z filtrowaniem po sprintId
    response_sprint_filtered = client.get("/api/projects/1/tasks?sprintId=200")
    assert response_sprint_filtered.status_code == 200
    sprint_filtered_tasks = cast(
        list[dict[str, object]], response_sprint_filtered.json()
    )
    assert len(sprint_filtered_tasks) == 2
    assert {cast(str, task["title"]) for task in sprint_filtered_tasks} == {
        "Task 2",
        "Task 3",
    }

    # Pobieramy z kombinacją filtrów
    response_combined_filtered = client.get(
        "/api/projects/1/tasks?status=Todo&assigneeId=10"
    )
    assert response_combined_filtered.status_code == 200
    combined_filtered_tasks = cast(
        list[dict[str, object]], response_combined_filtered.json()
    )
    assert len(combined_filtered_tasks) == 2
    assert {cast(str, task["title"]) for task in combined_filtered_tasks} == {
        "Task 1",
        "Task 3",
    }

    response_all_filters = client.get(
        "/api/projects/1/tasks?type=Bug&status=Todo&assigneeId=10&sprintId=100"
    )
    assert response_all_filters.status_code == 200
    all_filters_tasks = cast(list[dict[str, object]], response_all_filters.json())
    assert len(all_filters_tasks) == 1
    assert all_filters_tasks[0]["title"] == "Task 1"


def test_get_task_by_id(client: TestClient):
    """Test pobierania szczegółów konkretnego zadania."""
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Szczegółowy Task", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Szczegółowy Task"


def test_get_task_not_found(client: TestClient):
    """Test obsługi błędu przy braku zadania."""
    response = client.get("/api/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_task(client: TestClient):
    """Test edycji danych zadania."""
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Stary Tytuł", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    update_payload: Mapping[str, str | int] = {"title": "Nowy Tytuł", "storyPoints": 8}
    response = client.patch(f"/api/tasks/{task_id}", json=update_payload)

    assert response.status_code == 200
    data = cast(dict[str, object], response.json())
    assert data["title"] == "Nowy Tytuł"
    assert data["storyPoints"] == 8
    assert data["priority"] == "Medium"  # Niezmienione pole


def test_update_task_status(client: TestClient, db_session: Session):
    """Test zmiany statusu (Kanban drag & drop) - (UC7)."""
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Status Task", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    status_payload = {"status": "InProgress"}
    response = client.patch(f"/api/tasks/{task_id}/status", json=status_payload)

    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"
    logs = (
        db_session.query(models.ActivityLog)
        .filter(models.ActivityLog.work_item_id == task_id)
        .all()
    )
    assert len(logs) == 1

    user = (
        db_session.query(User)
        .filter(User.email == "tasks-test-user@example.com")
        .first()
    )
    assert user is not None

    log = logs[0]
    assert log.action == "STATUS_CHANGE"
    assert log.old_status == "ToDo"
    assert log.new_status == "InProgress"
    assert log.user_id == user.user_id


def test_delete_task(client: TestClient):
    """Test usuwania zadania."""
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Do usunięcia", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    # Usuwamy
    delete_response = client.delete(f"/api/tasks/{task_id}")
    assert delete_response.status_code == 204

    # Sprawdzamy czy na pewno zniknęło
    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404


def test_worklogs(client: TestClient, db_session: Session):
    """Test rejestrowania i pobierania logów czasu pracy."""
    # 1. Tworzymy zadanie
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Logowanie czasu", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    # 2. Dodajemy worklog
    worklog_payload: Mapping[str, str | float] = {
        "hoursSpent": 2.5,
        "note": "Praca nad testami",
    }
    log_response = client.post(f"/api/tasks/{task_id}/worklogs", json=worklog_payload)

    assert log_response.status_code == 201
    created_log = cast(dict[str, object], log_response.json())
    assert created_log["hoursSpent"] == 2.5
    assert created_log["note"] == "Praca nad testami"

    # 3. Pobieramy worklogi
    get_logs_response = client.get(f"/api/tasks/{task_id}/worklogs")
    assert get_logs_response.status_code == 200
    logs = cast(list[dict[str, object]], get_logs_response.json())
    assert len(logs) == 1
    first_log = logs[0]
    assert first_log["hoursSpent"] == 2.5
    created_log = (
        db_session.query(models.TimeLog)
        .filter(models.TimeLog.work_item_id == task_id)
        .first()
    )
    assert created_log is not None
    assert created_log.user_id > 0


def test_create_worklog_task_not_found(client: TestClient):
    response = client.post(
        "/api/tasks/999999/worklogs",
        json={"hoursSpent": 1.0, "note": "missing task"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_get_worklogs_task_not_found(client: TestClient):
    response = client.get("/api/tasks/999999/worklogs")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_protected_endpoints_require_auth(client: TestClient):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Auth check", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    app.dependency_overrides.pop(get_current_user, None)
    try:
        status_response = client.patch(f"/api/tasks/{task_id}/status", json={"status": "Done"})
        assert status_response.status_code == 401
        worklog_response = client.post(
            f"/api/tasks/{task_id}/worklogs",
            json={"hoursSpent": 1.0, "note": "unauthorized"},
        )
        assert worklog_response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_current_user, None)
