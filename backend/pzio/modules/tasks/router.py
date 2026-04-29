from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from pzio.db import get_db
from . import schemas, service

router = APIRouter(tags=["Tasks"])

# Mock dependency modułu Auth (do podmienienia przez zespół Auth)
def get_current_user_id():
    return 1 

@router.post("/api/projects/{id}/tasks", response_model=schemas.WorkItemResponse, status_code=status.HTTP_201_CREATED)
def create_task(id: int, task: schemas.WorkItemCreate, db: Session = Depends(get_db)):
    """Utworzenie nowego zadania w backlogu."""
    return service.create_work_item(db=db, project_id=id, task=task)

@router.get("/api/projects/{id}/tasks", response_model=List[schemas.WorkItemResponse])
def get_tasks(
    id: int,
    status: Optional[str] = None,
    assigneeId: Optional[int] = None,
    sprintId: Optional[int] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Pobranie zadań w projekcie z opcjonalnym filtrowaniem."""
    return service.get_work_items(db, project_id=id, status=status, assignee_id=assigneeId, sprint_id=sprintId, task_type=type)

@router.get("/api/tasks/{id}", response_model=schemas.WorkItemResponse)
def get_task(id: int, db: Session = Depends(get_db)):
    """Pobranie szczegółów zadania."""
    task = service.get_work_item(db, task_id=id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/api/tasks/{id}", response_model=schemas.WorkItemResponse)
def update_task(id: int, task_update: schemas.WorkItemUpdate, db: Session = Depends(get_db)):
    """Edycja szczegółów zadania (metoda PATCH)."""
    task = service.update_work_item(db, task_id=id, update_data=task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/api/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, db: Session = Depends(get_db)):
    """Usunięcie zadania."""
    success = service.delete_work_item(db, task_id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

@router.patch("/api/tasks/{id}/status", response_model=schemas.WorkItemResponse)
def update_task_status(
    id: int, 
    status_update: schemas.StatusUpdate, 
    db: Session = Depends(get_db), 
    user_id: int = Depends(get_current_user_id)
):
    """Zmiana statusu zadania (Kanban drag & drop). Zapisuje log audytowy."""
    task = service.update_work_item_status(db, task_id=id, new_status=status_update.status, user_id=user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/api/tasks/{id}/worklogs", response_model=schemas.TimeLogResponse, status_code=status.HTTP_201_CREATED)
def create_worklog(
    id: int, 
    worklog: schemas.TimeLogCreate, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Rejestrowanie czasu pracy (Worklog)."""
    return service.create_time_log(db, task_id=id, log_data=worklog, user_id=user_id)

@router.get("/api/tasks/{id}/worklogs", response_model=List[schemas.TimeLogResponse])
def get_worklogs(id: int, db: Session = Depends(get_db)):
    """Pobranie historii logów czasu pracy."""
    return service.get_time_logs(db, task_id=id)