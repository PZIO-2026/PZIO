import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importy z Twojej aplikacji
from pzio.modules.projects.router import router
from pzio.modules.projects.dependencies import get_db, get_current_user, CurrentUser
from pzio.db import Base  # Miejsce, gdzie zdefiniowane jest Base

# ===========================================================================
# Konfiguracja środowiska testowego
# ===========================================================================

# Baza danych w pamięci RAM (znika po wyłączeniu testów)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tworzymy testową instancję aplikacji i podpinamy Twój router
app = FastAPI()
app.include_router(router)


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


@pytest.fixture(scope="function")
def client(db_session):
    """Klient testowy podmieniający zależności (Dependency Overrides)."""
    
    # 1. Podmiana bazy danych
    def override_get_db():
        yield db_session

    # 2. Podmiana użytkownika na zalogowanego
    def override_get_current_user():
        return CurrentUser(id="mock-user-123", email="test@pzio.com")

    # Aplikowanie podmian
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c
        
    # Czyszczenie nadpisań po teście
    app.dependency_overrides.clear()


# ===========================================================================
# Przypadki Testowe
# ===========================================================================

def test_create_project(client: TestClient):
    payload = {
        "name": "Mój pierwszy projekt",
        "description": "Opis testowego projektu"
    }
    response = client.post("/api/projects", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Mój pierwszy projekt"
    assert "id" in data
    assert data["status"] == "active"


def test_list_projects(client: TestClient):
    # Najpierw tworzymy projekt w bazie
    client.post("/api/projects", json={"name": "Projekt A"})
    client.post("/api/projects", json={"name": "Projekt B"})
    
    response = client.get("/api/projects")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] in ["Projekt A", "Projekt B"]


def test_get_project_with_stats(client: TestClient):
    # Tworzymy projekt
    res = client.post("/api/projects", json={"name": "Projekt ze statystykami"})
    project_id = res.json()["id"]
    
    # Pobieramy szczegóły
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == project_id
    assert "stats" in data
    assert data["stats"]["member_count"] == 0
    assert data["stats"]["sprint_count"] == 0


def test_add_project_member(client: TestClient):
    # 1. Stwórz projekt
    proj_res = client.post("/api/projects", json={"name": "Projekt dla członków"})
    project_id = proj_res.json()["id"]
    
    # 2. Dodaj członka
    member_payload = {
        "userId": "user-456",
        "roles": ["developer", "scrum_master"]
    }
    response = client.post(f"/api/projects/{project_id}/members", json=member_payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user-456"
    assert "developer" in data["roles"]


def test_update_project(client: TestClient):
    # 1. Stwórz projekt
    proj_res = client.post("/api/projects", json={"name": "Stara nazwa"})
    project_id = proj_res.json()["id"]
    
    # 2. Zaktualizuj go (PATCH)
    response = client.patch(f"/api/projects/{project_id}", json={"name": "Nowa nazwa"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nowa nazwa"