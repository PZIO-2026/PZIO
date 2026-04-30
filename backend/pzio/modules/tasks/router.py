from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...db import get_db
from ..auth.deps import get_current_user
from ..auth.models import User
from . import schemas, service

router = APIRouter(tags=["Tasks"])


def get_current_user_id(current_user: User = Depends(get_current_user)) -> int:
    """Extract numeric actor identity from JWT-resolved auth user."""
    return current_user.user_id


DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[int, Depends(get_current_user_id)]


@router.post(
    "/api/projects/{id}/tasks",
    response_model=schemas.WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    id: int,
    task: schemas.WorkItemCreate,
    db: DbSession,
    _user_id: CurrentUserId,
):
    """Utworzenie nowego zadania w backlogu."""
    return service.create_work_item(db=db, project_id=id, task=task)


@router.get("/api/projects/{id}/tasks", response_model=list[schemas.WorkItemResponse])
def get_tasks(
    id: int,
    db: DbSession,
    _user_id: CurrentUserId,
    status: str | None = None,
    assignee_id: int | None = Query(default=None, alias="assigneeId"),
    sprint_id: int | None = Query(default=None, alias="sprintId"),
    task_type: str | None = Query(default=None, alias="type"),
):
    """Pobranie zadań w projekcie z opcjonalnym filtrowaniem."""
    return service.get_work_items(
        db,
        project_id=id,
        status=status,
        assignee_id=assignee_id,
        sprint_id=sprint_id,
        task_type=task_type,
    )


@router.get("/api/tasks/{id}", response_model=schemas.WorkItemResponse)
def get_task(
    id: int,
    db: DbSession,
):
    """Pobranie szczegółów zadania."""
    task = service.get_work_item(db, task_id=id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/api/tasks/{id}", response_model=schemas.WorkItemResponse)
def update_task(
    id: int,
    task_update: schemas.WorkItemUpdate,
    db: DbSession,
    _user_id: CurrentUserId,
):
    """Edycja szczegółów zadania (metoda PATCH)."""
    task = service.update_work_item(db, task_id=id, update_data=task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/api/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: int,
    db: DbSession,
    _user_id: CurrentUserId,
):
    """Usunięcie zadania."""
    success = service.delete_work_item(db, task_id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")


@router.patch("/api/tasks/{id}/status", response_model=schemas.WorkItemResponse)
def update_task_status(
    id: int,
    status_update: schemas.StatusUpdate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Zmiana statusu zadania (Kanban drag & drop). Zapisuje log audytowy."""
    task = service.update_work_item_status(
        db, task_id=id, new_status=status_update.status, user_id=user_id
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post(
    "/api/tasks/{id}/worklogs",
    response_model=schemas.TimeLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_worklog(
    id: int,
    worklog: schemas.TimeLogCreate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Rejestrowanie czasu pracy (Worklog)."""
    created_log = service.create_time_log(db, task_id=id, log_data=worklog, user_id=user_id)
    if not created_log:
        raise HTTPException(status_code=404, detail="Task not found")
    return created_log


@router.get("/api/tasks/{id}/worklogs", response_model=list[schemas.TimeLogResponse])
def get_worklogs(
    id: int,
    db: DbSession,
):
    """Pobranie historii logów czasu pracy."""
    logs = service.get_time_logs(db, task_id=id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return logs
