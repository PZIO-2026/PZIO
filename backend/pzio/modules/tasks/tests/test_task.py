from collections.abc import Mapping
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.main import app
from pzio.modules.auth.deps import get_current_user
from pzio.modules.auth.models import User, UserRole
from pzio.modules.auth.security import hash_password
from pzio.modules.admin.models import ActivityLog as AdminActivityLog
from pzio.modules.admin.models import TaskType
from pzio.modules.projects.models import Project, ProjectMember
from pzio.modules.tasks import models


@pytest.fixture(autouse=True)
def override_current_user(db_session: Session) -> None:
    for task_type_name in ("Task", "Bug"):
        task_type = (
            db_session.query(TaskType)
            .filter(TaskType.name == task_type_name)
            .first()
        )
        if task_type is None:
            db_session.add(TaskType(name=task_type_name))

    user = User(
        email="tasks-test-user@example.com",
        password_hash=hash_password("irrelevant"),
        first_name="Tasks",
        last_name="Tester",
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # The task endpoints now require the caller to be a member of the project,
    # so the fixture wires up project 1 with the test user as a member.
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.flush()
    db_session.add(
        ProjectMember(project_id=project.project_id, user_id=user.user_id, roles=["developer"])
    )
    db_session.commit()
    db_session.refresh(user)

    def _override_get_current_user() -> User:
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


def test_create_task_rejects_type_outside_dictionary(client: TestClient):
    response = client.post(
        "/api/projects/1/tasks",
        json={"title": "Nieznany typ", "type": "Anything", "priority": "High"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid task type"


def test_create_task_rejects_invalid_status(client: TestClient):
    response = client.post(
        "/api/projects/1/tasks",
        json={
            "title": "Nieznany status",
            "type": "Task",
            "priority": "High",
            "status": "Whatever",
        },
    )

    assert response.status_code == 400
    assert "status" in response.json()["detail"]


def test_create_task_rejects_invalid_priority(client: TestClient):
    response = client.post(
        "/api/projects/1/tasks",
        json={"title": "Nieznany priorytet", "type": "Task", "priority": "Urgent"},
    )

    assert response.status_code == 400
    assert "priority" in response.json()["detail"]


def test_create_task_rejects_empty_title_and_negative_story_points(
    client: TestClient,
):
    response = client.post(
        "/api/projects/1/tasks",
        json={
            "title": "   ",
            "type": "Task",
            "priority": "High",
            "storyPoints": -1,
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "title" in detail
    assert "storyPoints" in detail


def test_get_tasks(client: TestClient):
    """Test pobierania listy zadań w projekcie z filtrowaniem."""
    # Tworzymy zadania o różnych kombinacjach pól filtrowania
    create_response_1 = client.post(
        "/api/projects/1/tasks",
        json={
            "title": "Task 1",
            "type": "Bug",
            "priority": "Low",
            "status": "ToDo",
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
            "status": "InProgress",
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
            "status": "ToDo",
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
    assert [task["title"] for task in tasks] == ["Task 1", "Task 2", "Task 3"]

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


def test_update_task_rejects_type_outside_dictionary(client: TestClient):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Poprawny typ", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)

    response = client.patch(
        f"/api/tasks/{task_id_value}",
        json={"type": "Anything"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid task type"


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
    logs = db_session.query(AdminActivityLog).filter(AdminActivityLog.task_id == task_id).all()
    assert len(logs) == 2  # CREATE_TASK + STATUS_CHANGE

    user = (
        db_session.query(User)
        .filter(User.email == "tasks-test-user@example.com")
        .first()
    )
    assert user is not None

    log = logs[0]
    assert log.action == "CREATE_TASK"
    assert log.user_id == user.user_id

    log = logs[1]
    assert log.action == "STATUS_CHANGE"
    assert log.field_name == "status"
    assert log.old_value == "ToDo"
    assert log.new_value == "InProgress"
    assert log.user_id == user.user_id


def test_update_task_status_rejects_invalid_status(client: TestClient):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Status validation", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)

    response = client.patch(
        f"/api/tasks/{task_id_value}/status",
        json={"status": "Whatever"},
    )

    assert response.status_code == 400
    assert "status" in response.json()["detail"]


def test_update_task_status_does_not_log_when_status_is_unchanged(
    client: TestClient, db_session: Session
):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "No-op status", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    response = client.patch(f"/api/tasks/{task_id}/status", json={"status": "ToDo"})

    assert response.status_code == 200
    assert response.json()["status"] == "ToDo"
    logs = db_session.query(AdminActivityLog).filter(AdminActivityLog.task_id == task_id).all()
    assert len(logs) == 1  # Tylko CREATE_TASK, brak STATUS_CHANGE


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


def test_delete_task_preserves_activity_logs(client: TestClient, db_session: Session):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Audyt po usunieciu", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    status_response = client.patch(f"/api/tasks/{task_id}/status", json={"status": "Done"})
    assert status_response.status_code == 200

    delete_response = client.delete(f"/api/tasks/{task_id}")
    assert delete_response.status_code == 204

    logs = db_session.query(AdminActivityLog).filter(AdminActivityLog.task_id == task_id).all()
    assert len(logs) == 3  # CREATE_TASK + STATUS_CHANGE + DELETE_TASK
    assert logs[0].action == "CREATE_TASK"
    assert logs[1].action == "STATUS_CHANGE"
    assert logs[2].action == "DELETE_TASK"


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


def test_worklogs_reject_non_positive_hours(client: TestClient):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Walidacja czasu", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    zero_response = client.post(
        f"/api/tasks/{task_id}/worklogs",
        json={"hoursSpent": 0, "note": "zero"},
    )
    negative_response = client.post(
        f"/api/tasks/{task_id}/worklogs",
        json={"hoursSpent": -1, "note": "negative"},
    )

    assert zero_response.status_code == 400
    assert negative_response.status_code == 400
    assert "greater than 0" in zero_response.json()["detail"]
    assert "greater than 0" in negative_response.json()["detail"]


def test_worklogs_are_returned_in_creation_order(client: TestClient):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Kolejnosc worklogow", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    first_response = client.post(
        f"/api/tasks/{task_id}/worklogs",
        json={"hoursSpent": 1.0, "note": "first"},
    )
    second_response = client.post(
        f"/api/tasks/{task_id}/worklogs",
        json={"hoursSpent": 2.0, "note": "second"},
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(f"/api/tasks/{task_id}/worklogs")
    assert response.status_code == 200
    logs = cast(list[dict[str, object]], response.json())
    assert [log["note"] for log in logs] == ["first", "second"]


def test_work_item_relationships_include_worklogs_and_activity_logs(
    client: TestClient, db_session: Session
):
    create_resp = client.post(
        "/api/projects/1/tasks",
        json={"title": "Relacje ORM", "type": "Task", "priority": "Medium"},
    )
    created_task = cast(dict[str, object], create_resp.json())
    task_id_value = created_task["id"]
    assert isinstance(task_id_value, int)
    task_id = task_id_value

    worklog_response = client.post(
        f"/api/tasks/{task_id}/worklogs",
        json={"hoursSpent": 1.5, "note": "relationship"},
    )
    status_response = client.patch(f"/api/tasks/{task_id}/status", json={"status": "Done"})
    assert worklog_response.status_code == 201
    assert status_response.status_code == 200

    work_item = db_session.get(models.WorkItem, task_id)
    assert work_item is not None
    assert len(work_item.time_logs) == 1
    assert work_item.time_logs[0].note == "relationship"
    assert len(work_item.activity_logs) == 3  # CREATE_TASK + LOG_WORK + STATUS_CHANGE
    assert work_item.activity_logs[0].action == "CREATE_TASK"
    assert work_item.activity_logs[1].action == "LOG_WORK"
    assert work_item.activity_logs[2].action == "STATUS_CHANGE"


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


def test_non_member_cannot_access_project_tasks(client: TestClient, db_session: Session):
    """Użytkownik spoza projektu nie ma wglądu w zadania ani nie może ich tworzyć (#59)."""
    outsider = User(
        email="outsider@example.com",
        password_hash=hash_password("irrelevant"),
        first_name="Out",
        last_name="Sider",
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )
    db_session.add(outsider)
    db_session.commit()
    db_session.refresh(outsider)

    # Zadanie istniejące w projekcie 1 (do prób dostępu po id zadania).
    task = models.WorkItem(project_id=1, title="W projekcie", type="Task", priority="Medium")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    app.dependency_overrides[get_current_user] = lambda: outsider
    try:
        list_response = client.get("/api/projects/1/tasks")
        assert list_response.status_code == 403

        create_response = client.post(
            "/api/projects/1/tasks",
            json={"title": "Nielegalne zadanie", "type": "Task", "priority": "Medium"},
        )
        assert create_response.status_code == 403

        # Endpointy operujące po id zadania również wymagają członkostwa.
        assert client.get(f"/api/tasks/{task.id}").status_code == 403
        assert client.patch(f"/api/tasks/{task.id}", json={"title": "x"}).status_code == 403
        assert client.patch(f"/api/tasks/{task.id}/status", json={"status": "Done"}).status_code == 403
        assert client.delete(f"/api/tasks/{task.id}").status_code == 403
        assert client.get(f"/api/tasks/{task.id}/worklogs").status_code == 403
        worklog_resp = client.post(
            f"/api/tasks/{task.id}/worklogs", json={"hoursSpent": 1.0, "note": "x"}
        )
        assert worklog_resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


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
        task_response = client.get(f"/api/tasks/{task_id}")
        assert task_response.status_code == 401
        task_list_response = client.get("/api/projects/1/tasks")
        assert task_list_response.status_code == 401
        worklogs_response = client.get(f"/api/tasks/{task_id}/worklogs")
        assert worklogs_response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_current_user, None)
