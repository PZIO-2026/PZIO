from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from pzio.db import get_db
from pzio.modules.projects import schemas, service
from pzio.modules.projects.deps import get_current_user_mock

router = APIRouter(tags=["Projects"])

# ==========================================
# PROJEKTY (PROJECTS)
# ==========================================

@router.post("/api/projects", status_code=status.HTTP_201_CREATED, response_model=schemas.ProjectResponse)
def create_project(
    payload: schemas.ProjectCreate, 
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_mock) # Zabezpieczenie endpointu!
):
    project = service.create_project(db=db, payload=payload)
    # TODO: Pamiętajcie, że twórca projektu powinien automatycznie zostać do niego przypisany jako członek (ProjectMember)!
    return project

@router.get("/api/projects", response_model=schemas.PaginatedProjects)
def list_projects(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sortBy: Optional[str] = None,
    sortDirection: Optional[str] = "asc",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # TODO: Filtrowanie i paginacja projektów
    pass

@router.get("/api/projects/{id}", response_model=schemas.ProjectResponse)
def get_project_details(id: UUID, db: Session = Depends(get_db)):
    # TODO: Pobranie projektu wraz ze statystykami
    pass

@router.patch("/api/projects/{id}", response_model=schemas.ProjectResponse)
def update_project(id: UUID, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    # TODO: Aktualizacja wybranych pól
    pass

@router.delete("/api/projects/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(id: UUID, db: Session = Depends(get_db)):
    # TODO: Usunięcie/archiwizacja projektu
    pass

# ==========================================
# ZESPÓŁ (MEMBERS)
# ==========================================

@router.post("/api/projects/{id}/members", status_code=status.HTTP_201_CREATED, response_model=schemas.ProjectMemberResponse)
def add_project_member(id: UUID, payload: schemas.ProjectMemberAdd, db: Session = Depends(get_db)):
    # TODO: Dodanie rekordu ProjectMember
    pass

@router.get("/api/projects/{id}/members", response_model=List[schemas.ProjectMemberResponse])
def list_project_members(
    id: UUID,
    role: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # TODO: Pobranie listy przypisanych osób
    pass

@router.delete("/api/projects/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(id: UUID, user_id: UUID, db: Session = Depends(get_db)):
    # TODO: Usunięcie powiązania (ProjectMember)
    pass

# ==========================================
# SPRINTY (SPRINTS)
# ==========================================

@router.post("/api/projects/{id}/sprints", status_code=status.HTTP_201_CREATED, response_model=schemas.SprintResponse)
def create_sprint(id: UUID, payload: schemas.SprintCreate, db: Session = Depends(get_db)):
    # TODO: Tworzenie sprintu
    pass

@router.get("/api/projects/{id}/sprints", response_model=List[schemas.SprintResponse])
def list_sprints(id: UUID, db: Session = Depends(get_db)):
    # TODO: Zwraca sprinty danego projektu
    pass

@router.patch("/api/sprints/{id}", response_model=schemas.SprintResponse)
def update_sprint(id: UUID, payload: schemas.SprintUpdate, db: Session = Depends(get_db)):
    # TODO: Aktualizacja/Start sprintu
    pass

@router.delete("/api/sprints/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(id: UUID, db: Session = Depends(get_db)):
    # TODO: Usunięcie sprintu
    pass

@router.get("/api/sprints/{id}/burndown", response_model=schemas.BurndownResponse)
def get_sprint_burndown(id: UUID, db: Session = Depends(get_db)):
    # TODO: Zaawansowana agregacja z bazy (wymaga logiki Modułu Zadań)
    pass