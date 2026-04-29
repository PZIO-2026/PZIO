from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from pzio.config import settings
from pzio.db import get_db
from pzio.modules.admin import service
from pzio.modules.admin.schemas import (
    ActivityLogRead,
    BackupRead,
    TaskTypeCreate,
    TaskTypeRead,
)
from pzio.modules.auth.deps import get_current_user, require_admin
from pzio.modules.auth.models import User

# Endpoints in this module: see SAD §4.5 (paths /api/admin/*, /api/task-types,
# /api/tasks/{id}/history). Full paths are declared on each route — no router-level
# prefix is set because the admin module owns multiple URL roots.
router = APIRouter(tags=["Admin"])


@router.post(
    "/api/admin/task-types",
    response_model=TaskTypeRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Add a task type (Admin)",
    description="Adds a new task type to the system dictionary. Requires Administrator role.",
    responses={
        201: {"description": "Task type created"},
        400: {"description": "Validation error"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Insufficient privileges"},
        409: {"description": "Task type with this name already exists"},
    },
)
def add_task_type(
    payload: TaskTypeCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> TaskTypeRead:
    try:
        task_type = service.create_task_type(db, payload)
    except service.TaskTypeAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task type with this name already exists",
        )
    return TaskTypeRead.model_validate(task_type)


@router.get(
    "/api/task-types",
    response_model=list[TaskTypeRead],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get task type dictionary",
    description="Returns the list of task types defined in the system.",
    responses={
        200: {"description": "List of task types"},
        401: {"description": "Missing or invalid token"},
    },
)
def get_task_types(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[TaskTypeRead]:
    items = service.list_task_types(db)
    return [TaskTypeRead.model_validate(item) for item in items]


@router.post(
    "/api/admin/backups",
    response_model=BackupRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Force a database backup (Admin)",
    description="Triggers a file-level copy of the SQLite database into the configured "
    "backup directory. Requires Administrator role.",
    responses={
        201: {"description": "Backup created"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Insufficient privileges"},
        500: {"description": "Backup failed"},
    },
)
def force_backup(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BackupRead:
    try:
        record = service.create_backup(db, settings.database_url, settings.backup_dir)
    except service.BackupFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {exc}",
        )
    return BackupRead(
        backup_id=record.backup_id,
        timestamp=record.created_at,
        status=record.status,
    )


@router.get(
    "/api/tasks/{task_id}/history",
    response_model=list[ActivityLogRead],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Get task change history",
    description="Returns the audit log entries for a task in chronological order.",
    responses={
        200: {"description": "List of audit entries"},
        401: {"description": "Missing or invalid token"},
    },
)
def get_task_history(
    task_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[ActivityLogRead]:
    entries = service.get_task_history(db, task_id)
    return [ActivityLogRead.model_validate(entry) for entry in entries]
