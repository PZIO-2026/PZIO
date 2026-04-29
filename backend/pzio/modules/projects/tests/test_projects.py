"""
Używa SQLite in-memory jako bazy danych.
Podmienia zależności get_db i get_current_user przez FastAPI Dependency Overrides.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pzio.db import Base
from pzio.modules.auth.models import User, UserRole
from pzio.modules.projects.router import router
from pzio.modules.projects.dependencies import get_db, get_current_user

# ---------------------------------------------------------------------------
# TEST ENV CONFIG
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(router)


# ---------------------------------------------------------------------------
# MOCK USERS
# ---------------------------------------------------------------------------

def _make_user(user_id: int, email: str = None) -> User:
    return User(
        user_id=user_id,
        email=email or f"user{user_id}@pzio.com",
        password_hash="irrelevant",
        first_name="Test",
        last_name="User",
        role=UserRole.TEAM_MEMBER,
        is_active=True,
    )


MOCK_USER = _make_user(1, "test@pzio.com")
OTHER_USER = _make_user(2, "other@pzio.com")


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """Tworzy schemat bazy przed każdym testem i usuwa po teście."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def _make_client(db_session, user: User) -> TestClient:
    """Buduje klienta HTTP z podanym użytkownikiem jako zalogowanym."""
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)


@pytest.fixture(scope="function")
def client(db_session):
    """Klient testowy z domyślnym użytkownikiem (MOCK_USER, id=1)."""
    c = _make_client(db_session, MOCK_USER)
    with c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def other_client(db_session):
    """Klient testowy dla innego użytkownika (OTHER_USER, id=2)."""
    c = _make_client(db_session, OTHER_USER)
    with c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _create_project(client: TestClient, name: str = "Projekt testowy", description: str | None = None) -> dict:
    payload: dict = {"name": name}
    if description:
        payload["description"] = description
    res = client.post("/api/projects", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def _create_sprint(client: TestClient, project_id: int, name: str = "Sprint 1") -> dict:
    payload = {
        "name": name,
        "startDate": "2025-01-01T00:00:00Z",
        "endDate": "2025-01-14T00:00:00Z",
    }
    res = client.post(f"/api/projects/{project_id}/sprints", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def _add_member(client: TestClient, project_id: int, user_id: int, roles: list[str]) -> dict:
    res = client.post(
        f"/api/projects/{project_id}/members",
        json={"userId": user_id, "roles": roles},
    )
    assert res.status_code == 201, res.text
    return res.json()


# ---------------------------------------------------------------------------
# PROJECTS – CRUD
# ---------------------------------------------------------------------------

class TestCreateProject:
    def test_returns_201_and_correct_fields(self, client: TestClient):
        data = _create_project(client, name="Nowy projekt", description="Opis")

        assert data["name"] == "Nowy projekt"
        assert data["description"] == "Opis"
        assert data["status"] == "active"
        assert "projectId" in data
        assert isinstance(data["projectId"], int)
        assert "createdAt" in data
        assert "updatedAt" in data

    def test_description_is_optional(self, client: TestClient):
        data = _create_project(client, name="Bez opisu")
        assert data["description"] is None

    def test_missing_name_returns_422(self, client: TestClient):
        res = client.post("/api/projects", json={"description": "Bez nazwy"})
        assert res.status_code == 422

    def test_empty_name_returns_422(self, client: TestClient):
        res = client.post("/api/projects", json={"name": ""})
        assert res.status_code == 422


class TestListProjects:
    def test_returns_empty_page_when_no_projects(self, client: TestClient):
        res = client.get("/api/projects")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_returns_only_own_projects(self, client: TestClient, other_client: TestClient, db_session):
        """Użytkownik widzi tylko projekty, do których należy."""
        # client (user=1) tworzy projekt i dodaje siebie jako member
        proj = _create_project(client, "Mój projekt")
        pid = proj["projectId"]

        # other_client (user=2) tworzy swój projekt i dodaje siebie
        # ale musi użyć osobnej sesji — tu upraszczamy przez bezpośredni insert
        # W praktyce: other_client tworzy projekt + dodaje siebie.
        # Ponieważ fixtures share db_session, wywołujemy przez other_client:
        proj2 = _create_project(other_client, "Cudzy projekt")
        pid2 = proj2["projectId"]

        res = client.get("/api/projects")
        data = res.json()
        ids = [p["projectId"] for p in data["items"]]
        assert pid in ids
        assert pid2 not in ids

    def test_returns_all_member_projects(self, client: TestClient):
        proj_a = _create_project(client, "Projekt A")
        proj_b = _create_project(client, "Projekt B")
        _add_member(client, proj_a["projectId"], MOCK_USER.user_id, ["developer"])
        _add_member(client, proj_b["projectId"], MOCK_USER.user_id, ["developer"])

        res = client.get("/api/projects")
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_pagination(self, client: TestClient):
        for i in range(5):
            proj = _create_project(client, f"Projekt {i}")
            _add_member(client, proj["projectId"], MOCK_USER.user_id, ["developer"])

        res = client.get("/api/projects?page=1&size=2")
        data = res.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2

    def test_search_by_name(self, client: TestClient):
        proj_a = _create_project(client, "Alpha")
        proj_b = _create_project(client, "Beta")
        _add_member(client, proj_a["projectId"], MOCK_USER.user_id, ["developer"])
        _add_member(client, proj_b["projectId"], MOCK_USER.user_id, ["developer"])

        res = client.get("/api/projects?search=Alpha")
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Alpha"

    def test_filter_by_status_active(self, client: TestClient):
        proj_active = _create_project(client, "Aktywny")
        proj_to_archive = _create_project(client, "Do archiwum")
        _add_member(client, proj_active["projectId"], MOCK_USER.user_id, ["developer"])
        _add_member(client, proj_to_archive["projectId"], MOCK_USER.user_id, ["developer"])

        client.delete(f"/api/projects/{proj_to_archive['projectId']}")

        res = client.get("/api/projects?status=active")
        data = res.json()
        assert all(p["status"] == "active" for p in data["items"])
        ids = [p["projectId"] for p in data["items"]]
        assert proj_to_archive["projectId"] not in ids

    def test_sort_by_name_asc(self, client: TestClient):
        for name in ["Zeta", "Alpha", "Mu"]:
            proj = _create_project(client, name)
            _add_member(client, proj["projectId"], MOCK_USER.user_id, ["developer"])

        res = client.get("/api/projects?sortBy=name&sortDirection=asc")
        names = [p["name"] for p in res.json()["items"]]
        assert names == sorted(names)


class TestGetProject:
    def test_returns_project_with_stats(self, client: TestClient):
        proj = _create_project(client, "Z statystykami")
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.get(f"/api/projects/{pid}")
        assert res.status_code == 200
        data = res.json()

        assert data["projectId"] == pid
        assert "stats" in data
        assert data["stats"]["memberCount"] == 1
        assert data["stats"]["sprintCount"] == 0

    def test_stats_reflect_added_members_and_sprints(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])
        _add_member(client, pid, 99, ["developer"])
        _create_sprint(client, pid)

        res = client.get(f"/api/projects/{pid}")
        stats = res.json()["stats"]
        assert stats["memberCount"] == 2
        assert stats["sprintCount"] == 1

    def test_nonexistent_project_returns_404(self, client: TestClient):
        res = client.get("/api/projects/99999")
        assert res.status_code == 404

    def test_non_member_cannot_view_project(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu dostaje 403."""
        proj = _create_project(client, "Tajny projekt")
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = other_client.get(f"/api/projects/{pid}")
        assert res.status_code == 403


class TestUpdateProject:
    def test_patch_name(self, client: TestClient):
        proj = _create_project(client, "Stara nazwa")
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.patch(f"/api/projects/{pid}", json={"name": "Nowa nazwa"})
        assert res.status_code == 200
        assert res.json()["name"] == "Nowa nazwa"

    def test_patch_description(self, client: TestClient):
        proj = _create_project(client, "Projekt", "Stary opis")
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.patch(f"/api/projects/{pid}", json={"description": "Nowy opis"})
        assert res.status_code == 200
        assert res.json()["description"] == "Nowy opis"

    def test_empty_patch_returns_400(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.patch(f"/api/projects/{pid}", json={})
        assert res.status_code == 400

    def test_patch_nonexistent_returns_404(self, client: TestClient):
        res = client.patch("/api/projects/99999", json={"name": "X"})
        assert res.status_code == 404

    def test_non_member_cannot_update_project(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie może edytować projektu."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = other_client.patch(f"/api/projects/{pid}", json={"name": "Hack"})
        assert res.status_code == 403


class TestDeleteProject:
    def test_soft_delete_returns_204(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.delete(f"/api/projects/{pid}")
        assert res.status_code == 204

    def test_soft_delete_sets_status_archived(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        client.delete(f"/api/projects/{pid}")

        res = client.get(f"/api/projects/{pid}")
        assert res.json()["status"] == "archived"

    def test_delete_nonexistent_returns_404(self, client: TestClient):
        res = client.delete("/api/projects/99999")
        assert res.status_code == 404

    def test_non_member_cannot_delete_project(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie może go archiwizować."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = other_client.delete(f"/api/projects/{pid}")
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# PROJECT MEMBERS
# ---------------------------------------------------------------------------

class TestProjectMembers:
    def test_add_member_returns_201(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 42, "roles": ["developer"]},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["userId"] == 42
        assert "developer" in data["roles"]
        assert data["projectId"] == pid
        assert "joinedAt" in data

    def test_add_member_multiple_roles(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["project_owner"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 10, "roles": ["developer", "scrum_master"]},
        )
        assert res.status_code == 201
        assert set(res.json()["roles"]) == {"developer", "scrum_master"}

    def test_add_duplicate_member_returns_409(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])

        payload = {"userId": 55, "roles": ["developer"]}
        client.post(f"/api/projects/{pid}/members", json=payload)
        res = client.post(f"/api/projects/{pid}/members", json=payload)
        assert res.status_code == 409

    def test_add_member_to_nonexistent_project_returns_404(self, client: TestClient):
        res = client.post(
            "/api/projects/99999/members",
            json={"userId": 1, "roles": ["developer"]},
        )
        assert res.status_code == 404

    def test_invalid_role_returns_422(self, client: TestClient):
        """Nieznana rola powinna być odrzucona przez Pydantic (422)."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 50, "roles": ["manager"]},  # nieistniejąca rola
        )
        assert res.status_code == 422

    def test_empty_roles_returns_422(self, client: TestClient):
        """Lista ról nie może być pusta."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 50, "roles": []},
        )
        assert res.status_code == 422

    def test_developer_cannot_add_member(self, client: TestClient):
        """Developer nie może dodawać członków do projektu."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 99, "roles": ["developer"]},
        )
        assert res.status_code == 403

    def test_qa_cannot_add_member(self, client: TestClient):
        """QA nie może dodawać członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["qa"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 99, "roles": ["developer"]},
        )
        assert res.status_code == 403

    def test_scrum_master_can_add_member(self, client: TestClient):
        """Scrum Master może dodawać członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 99, "roles": ["developer"]},
        )
        assert res.status_code == 201

    def test_project_owner_can_add_member(self, client: TestClient):
        """Project Owner może dodawać członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["project_owner"])

        res = client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 99, "roles": ["developer"]},
        )
        assert res.status_code == 201

    def test_non_member_cannot_add_member(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie może dodawać członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])

        res = other_client.post(
            f"/api/projects/{pid}/members",
            json={"userId": 99, "roles": ["developer"]},
        )
        assert res.status_code == 403

    def test_list_members(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])
        _add_member(client, pid, 10, ["developer"])
        _add_member(client, pid, 20, ["qa"])

        res = client.get(f"/api/projects/{pid}/members")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 3

    def test_non_member_cannot_list_members(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie widzi listy członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = other_client.get(f"/api/projects/{pid}/members")
        assert res.status_code == 403

    def test_developer_cannot_remove_member(self, client: TestClient):
        """Developer nie może usuwać członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        _add_member(client, pid, 77, ["qa"])

        res = client.delete(f"/api/projects/{pid}/members/77")
        assert res.status_code == 403

    def test_scrum_master_can_remove_member(self, client: TestClient):
        """Scrum Master może usuwać członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])
        _add_member(client, pid, 77, ["developer"])

        res = client.delete(f"/api/projects/{pid}/members/77")
        assert res.status_code == 204

    def test_project_owner_can_remove_member(self, client: TestClient):
        """Project Owner może usuwać członków."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["project_owner"])
        _add_member(client, pid, 77, ["developer"])

        res = client.delete(f"/api/projects/{pid}/members/77")
        assert res.status_code == 204

    def test_remove_member_actually_removes(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])
        _add_member(client, pid, 77, ["developer"])

        client.delete(f"/api/projects/{pid}/members/77")

        res = client.get(f"/api/projects/{pid}/members")
        user_ids = [m["userId"] for m in res.json()["items"]]
        assert 77 not in user_ids

    def test_remove_nonexistent_member_returns_404(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["scrum_master"])

        res = client.delete(f"/api/projects/{pid}/members/99999")
        assert res.status_code == 404

    def test_non_member_cannot_remove_member(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie może usunąć członka."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["project_owner"])
        _add_member(client, pid, 77, ["developer"])

        res = other_client.delete(f"/api/projects/{pid}/members/77")
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# SPRINTS
# ---------------------------------------------------------------------------

class TestSprints:
    def test_create_sprint_returns_201(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.post(
            f"/api/projects/{pid}/sprints",
            json={
                "name": "Sprint 1",
                "startDate": "2025-03-01T00:00:00Z",
                "endDate": "2025-03-14T00:00:00Z",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Sprint 1"
        assert data["status"] == "planned"
        assert data["projectId"] == pid
        assert "sprintId" in data
        assert isinstance(data["sprintId"], int)

    def test_create_sprint_invalid_dates_returns_400(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.post(
            f"/api/projects/{pid}/sprints",
            json={
                "name": "Zły sprint",
                "startDate": "2025-03-14T00:00:00Z",
                "endDate": "2025-03-01T00:00:00Z",
            },
        )
        assert res.status_code == 400

    def test_create_sprint_equal_dates_returns_400(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = client.post(
            f"/api/projects/{pid}/sprints",
            json={
                "name": "Równe daty",
                "startDate": "2025-03-01T00:00:00Z",
                "endDate": "2025-03-01T00:00:00Z",
            },
        )
        assert res.status_code == 400

    def test_non_member_cannot_create_sprint(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie może tworzyć sprintów."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        res = other_client.post(
            f"/api/projects/{pid}/sprints",
            json={
                "name": "Nielegalny sprint",
                "startDate": "2025-03-01T00:00:00Z",
                "endDate": "2025-03-14T00:00:00Z",
            },
        )
        assert res.status_code == 403

    def test_list_sprints_ordered_by_start_date(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])

        client.post(f"/api/projects/{pid}/sprints", json={
            "name": "Sprint 2",
            "startDate": "2025-02-01T00:00:00Z",
            "endDate": "2025-02-14T00:00:00Z",
        })
        client.post(f"/api/projects/{pid}/sprints", json={
            "name": "Sprint 1",
            "startDate": "2025-01-01T00:00:00Z",
            "endDate": "2025-01-14T00:00:00Z",
        })

        res = client.get(f"/api/projects/{pid}/sprints")
        assert res.status_code == 200
        names = [s["name"] for s in res.json()]
        assert names == ["Sprint 1", "Sprint 2"]

    def test_non_member_cannot_list_sprints(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie widzi sprintów."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        _create_sprint(client, pid)

        res = other_client.get(f"/api/projects/{pid}/sprints")
        assert res.status_code == 403

    def test_update_sprint_name(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = client.patch(f"/api/sprints/{sprint['sprintId']}", json={"name": "Nowa nazwa sprintu"})
        assert res.status_code == 200
        assert res.json()["name"] == "Nowa nazwa sprintu"

    def test_update_sprint_status(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = client.patch(f"/api/sprints/{sprint['sprintId']}", json={"status": "active"})
        assert res.status_code == 200
        assert res.json()["status"] == "active"

    def test_update_sprint_empty_body_returns_400(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = client.patch(f"/api/sprints/{sprint['sprintId']}", json={})
        assert res.status_code == 400

    def test_non_member_cannot_update_sprint(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie może edytować sprintu."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = other_client.patch(
            f"/api/sprints/{sprint['sprintId']}",
            json={"name": "Hack"},
        )
        assert res.status_code == 403

    def test_delete_sprint_returns_204(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = client.delete(f"/api/sprints/{sprint['sprintId']}")
        assert res.status_code == 204

    def test_delete_sprint_removes_from_list(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        client.delete(f"/api/sprints/{sprint['sprintId']}")

        res = client.get(f"/api/projects/{pid}/sprints")
        assert res.json() == []

    def test_delete_nonexistent_sprint_returns_404(self, client: TestClient):
        res = client.delete("/api/sprints/99999")
        assert res.status_code == 404

    def test_non_member_cannot_delete_sprint(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie może usunąć sprintu."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = other_client.delete(f"/api/sprints/{sprint['sprintId']}")
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# BURNDOWN CHART
# ---------------------------------------------------------------------------

class TestBurndown:
    def test_burndown_returns_200(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = client.get(f"/api/sprints/{sprint['sprintId']}/burndown")
        assert res.status_code == 200

    def test_burndown_structure(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)
        sid = sprint["sprintId"]

        data = client.get(f"/api/sprints/{sid}/burndown").json()
        assert data["sprintId"] == sid
        assert "totalPoints" in data
        assert isinstance(data["days"], list)
        assert len(data["days"]) > 0

    def test_burndown_days_have_correct_fields(self, client: TestClient):
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)
        sid = sprint["sprintId"]

        days = client.get(f"/api/sprints/{sid}/burndown").json()["days"]
        for day in days:
            assert "date" in day
            assert "remainingPoints" in day
            assert isinstance(day["remainingPoints"], int)

    def test_burndown_nonexistent_sprint_returns_404(self, client: TestClient):
        res = client.get("/api/sprints/99999/burndown")
        assert res.status_code == 404

    def test_non_member_cannot_view_burndown(self, client: TestClient, other_client: TestClient):
        """Użytkownik spoza projektu nie ma dostępu do burndown chart."""
        proj = _create_project(client)
        pid = proj["projectId"]
        _add_member(client, pid, MOCK_USER.user_id, ["developer"])
        sprint = _create_sprint(client, pid)

        res = other_client.get(f"/api/sprints/{sprint['sprintId']}/burndown")
        assert res.status_code == 403