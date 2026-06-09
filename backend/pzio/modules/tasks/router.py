from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...db import get_db
from ..auth.deps import get_current_user
from ..auth.models import User
from ..projects import services as projects_service
from . import models, schemas, service

router = APIRouter(tags=["Tasks"])


def get_current_user_id(current_user: User = Depends(get_current_user)) -> int:
    """Extract numeric actor identity from JWT-resolved auth user."""
    return current_user.user_id


DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[int, Depends(get_current_user_id)]


def _require_member_for_task(db: Session, task_id: int, user_id: int) -> models.WorkItem:
    """Load a task and ensure the caller is a member of its project.

    Raises 404 when the task does not exist (without leaking membership) and 403
    when the caller is not a member of the owning project.
    """
    task = service.get_work_item(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    projects_service.require_project_member(db, project_id=task.project_id, user_id=user_id)
    return task


@router.post(
    "/api/projects/{id}/tasks",
    response_model=schemas.WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        403: {"description": "Caller is not a member of the project"},
        404: {"description": "Project not found"},
    },
)
def create_task(
    id: int,
    task: schemas.WorkItemCreate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Utworzenie nowego zadania w backlogu."""
    projects_service.require_project_member(db, project_id=id, user_id=user_id)
    return service.create_work_item(db=db, project_id=id, task=task, user_id=user_id)


@router.get(
    "/api/projects/{id}/tasks",
    response_model=list[schemas.WorkItemResponse],
    responses={
        403: {"description": "Caller is not a member of the project"},
        404: {"description": "Project not found"},
    },
)
def get_tasks(
    id: int,
    db: DbSession,
    user_id: CurrentUserId,
    status: str | None = None,
    assignee_id: int | None = Query(default=None, alias="assigneeId"),
    sprint_id: int | None = Query(default=None, alias="sprintId"),
    task_type: str | None = Query(default=None, alias="type"),
):
    """Pobranie zadań w projekcie z opcjonalnym filtrowaniem."""
    projects_service.require_project_member(db, project_id=id, user_id=user_id)
    return service.get_work_items(
        db,
        project_id=id,
        status=status,
        assignee_id=assignee_id,
        sprint_id=sprint_id,
        task_type=task_type,
    )


@router.get(
    "/api/tasks/{id}",
    response_model=schemas.WorkItemResponse,
    responses={403: {"description": "Caller is not a member of the project"}},
)
def get_task(
    id: int,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Pobranie szczegółów zadania."""
    return _require_member_for_task(db, task_id=id, user_id=user_id)


@router.patch(
    "/api/tasks/{id}",
    response_model=schemas.WorkItemResponse,
    responses={403: {"description": "Caller is not a member of the project"}},
)
def update_task(
    id: int,
    task_update: schemas.WorkItemUpdate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Edycja szczegółów zadania (metoda PATCH)."""
    _require_member_for_task(db, task_id=id, user_id=user_id)
    task = service.update_work_item(db, task_id=id, update_data=task_update, user_id=user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete(
    "/api/tasks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"description": "Caller is not a member of the project"}},
)
def delete_task(
    id: int,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Usunięcie zadania."""
    _require_member_for_task(db, task_id=id, user_id=user_id)
    success = service.delete_work_item(db, task_id=id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")


@router.patch(
    "/api/tasks/{id}/status",
    response_model=schemas.WorkItemResponse,
    responses={403: {"description": "Caller is not a member of the project"}},
)
def update_task_status(
    id: int,
    status_update: schemas.StatusUpdate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Zmiana statusu zadania (Kanban drag & drop). Zapisuje log audytowy."""
    _require_member_for_task(db, task_id=id, user_id=user_id)
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
    responses={403: {"description": "Caller is not a member of the project"}},
)
def create_worklog(
    id: int,
    worklog: schemas.TimeLogCreate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Rejestrowanie czasu pracy (Worklog)."""
    _require_member_for_task(db, task_id=id, user_id=user_id)
    created_log = service.create_time_log(db, task_id=id, log_data=worklog, user_id=user_id)
    if not created_log:
        raise HTTPException(status_code=404, detail="Task not found")
    return created_log


@router.get(
    "/api/tasks/{id}/worklogs",
    response_model=list[schemas.TimeLogResponse],
    responses={403: {"description": "Caller is not a member of the project"}},
)
def get_worklogs(
    id: int,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Pobranie historii logów czasu pracy."""
    _require_member_for_task(db, task_id=id, user_id=user_id)
    logs = service.get_time_logs(db, task_id=id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return logs
