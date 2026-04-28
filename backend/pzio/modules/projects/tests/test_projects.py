from fastapi.testclient import TestClient
from pzio.main import app

# Inicjalizujemy wirtualnego klienta, który będzie udawał przeglądarkę
client = TestClient(app)

def test_create_project_success():
    """Test sprawdza czy poprawne dane utworzą projekt (Zwrócą 201 Created)"""
    headers = {"Authorization": "Bearer sztuczny-token-z-mocka"}
    payload = {
        "name": "Projekt Apollo",
        "description": "Lot na księżyc"
    }
    
    response = client.post("/api/projects", json=payload, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Projekt Apollo"
    assert data["status"] == "Aktywny"
    assert "id" in data # Sprawdzamy czy baza wygenerowała UUID

def test_create_project_unauthorized():
    """Test sprawdza czy brak tokenu zostanie zablokowany (401 Unauthorized)"""
    payload = {
        "name": "Projekt Hack",
        "description": "Próba włamania"
    }
    
    # Wysyłamy zapytanie BEZ nagłówka headers
    response = client.post("/api/projects", json=payload)
    
    assert response.status_code == 401
    assert response.json() == {"detail": "Brak tokenu autoryzacji"}

def test_create_project_bad_request():
    """Test sprawdza czy błędny JSON (brak nazwy) zostanie odrzucony (400 Bad Request)"""
    headers = {"Authorization": "Bearer sztuczny-token"}
    payload = {
        "description": "Zapomnieliśmy nazwy projektu"
    }
    
    response = client.post("/api/projects", json=payload, headers=headers)
    
    # Sprawdzamy czy zadziałał customowy handler błędów Tech Leada (zwraca 400, a nie 422)
    assert response.status_code == 400 
    assert "name" in response.json()["detail"]