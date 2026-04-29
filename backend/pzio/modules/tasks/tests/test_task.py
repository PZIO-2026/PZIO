from collections.abc import Mapping
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importy z aplikacji (zakładam standardową strukturę inicjalizacji FastAPI w pzio.main)
from ....db import Base, get_db
from ....main import app
from ...auth.deps import get_current_user
from ...auth.models import User, UserRole
from ...auth.security import hash_password
from .. import models

# 1. Konfiguracja testowej bazy danych (In-Memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2. Nadpisywanie zależności (Dependency Injection)
def override_get_db():
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()


def override_get_current_user() -> User:
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "tasks-test-user@example.com").first()
        if user is None:
            user = User(
                email="tasks-test-user@example.com",
                password_hash=hash_password("irrelevant"),
                first_name="Tasks",
                last_name="Tester",
                role=UserRole.TEAM_MEMBER,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


client = TestClient(app)


# 3. Fixture przygotowujący czystą bazę przed każdym testem
@pytest.fixture(autouse=True)
def setup_database():
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides = original_overrides


# --- TESTY ENDPOINTÓW ---


def test_create_task():
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


def test_get_tasks():
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


def test_get_task_by_id():
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


def test_get_task_not_found():
    """Test obsługi błędu przy braku zadania."""
    response = client.get("/api/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_task():
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


def test_update_task_status():
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
    db = TestingSessionLocal()
    try:
        log = db.query(models.ActivityLog).filter(models.ActivityLog.work_item_id == task_id).first()
        assert log is not None
        assert log.user_id > 0
    finally:
        db.close()


def test_delete_task():
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


def test_worklogs():
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
    db = TestingSessionLocal()
    try:
        created_log = db.query(models.TimeLog).filter(models.TimeLog.work_item_id == task_id).first()
        assert created_log is not None
        assert created_log.user_id > 0
    finally:
        db.close()


def test_protected_endpoints_require_auth():
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
        app.dependency_overrides[get_current_user] = override_get_current_user
