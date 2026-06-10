from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pzio.modules.admin import service as admin_service
from pzio.modules.admin.models import TaskType
from pzio.modules.tasks import models, schemas


def _normalize_status_value(value: str) -> str:
    return "".join(value.lower().split())


def _validate_task_type(db: Session, task_type: str) -> None:
    statement = select(TaskType).where(TaskType.name == task_type)
    if db.execute(statement).scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task type",
        )


def _get_descendants(db: Session, task_id: int) -> list[models.WorkItem]:
    descendants: list[models.WorkItem] = []
    pending_parent_ids = [task_id]

    while pending_parent_ids:
        statement = (
            select(models.WorkItem)
            .where(models.WorkItem.parent_id.in_(pending_parent_ids))
            .order_by(models.WorkItem.id.asc())
        )
        children = list(db.scalars(statement).all())
        if not children:
            break
        descendants.extend(children)
        pending_parent_ids = [child.id for child in children]

    return descendants


def _validate_parent(
    db: Session,
    *,
    project_id: int,
    task_id: int | None,
    parent_id: int | None,
) -> models.WorkItem | None:
    if parent_id is None:
        return None

    parent = get_work_item(db, parent_id)
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie znaleziono zadania nadrzędnego",
        )
    if parent.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zadanie nadrzędne musi należeć do tego samego projektu",
        )
    if task_id is not None and parent.id == task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zadanie nie może być swoim własnym zadaniem nadrzędnym",
        )

    current = parent
    while current.parent_id is not None:
        if current.parent_id == task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hierarchia zadań nie może zawierać cykli",
            )
        current = get_work_item(db, current.parent_id)
        if current is None:
            break

    return parent


def _validate_parent_sprint(parent: models.WorkItem | None, sprint_id: int | None) -> None:
    if parent is None:
        return
    if parent.sprint_id != sprint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zadanie podrzędne musi należeć do tego samego sprintu co jego zadanie nadrzędne",
        )


def _cascade_sprint_to_descendants(
    db: Session,
    *,
    task_id: int,
    sprint_id: int | None,
    user_id: int,
) -> None:
    descendants = _get_descendants(db, task_id)
    changed_descendants = [
        (child, child.sprint_id) for child in descendants if child.sprint_id != sprint_id
    ]
    if not changed_descendants:
        return

    for child, _old_sprint_id in changed_descendants:
        child.sprint_id = sprint_id
    db.commit()

    for child, old_sprint_id in changed_descendants:
        admin_service.log_activity(
            db,
            task_id=child.id,
            user_id=user_id,
            action="UPDATE_FIELD",
            field_name="sprint_id",
            old_value=str(old_sprint_id) if old_sprint_id is not None else None,
            new_value=str(sprint_id) if sprint_id is not None else None,
        )


def _delete_work_item_tree(
    db: Session,
    *,
    task_id: int,
    user_id: int,
) -> bool:
    db_item = get_work_item(db, task_id)
    if not db_item:
        return False

    descendants = _get_descendants(db, task_id)
    items_to_delete = list(reversed(descendants)) + [db_item]
    deleted_ids = [item.id for item in items_to_delete]

    for item in items_to_delete:
        db.delete(item)
        # Flush each delete so self-referential FK checks see children removed
        # before their parent. Postgres can batch deletes otherwise.
        db.flush()
    db.commit()

    for deleted_id in deleted_ids:
        admin_service.log_activity(
            db,
            task_id=deleted_id,
            user_id=user_id,
            action="DELETE_TASK",
        )

    return True


def create_work_item(
    db: Session,
    project_id: int,
    task: schemas.WorkItemCreate,
    user_id: int,
) -> models.WorkItem:
    _validate_task_type(db, task.type)
    parent = _validate_parent(db, project_id=project_id, task_id=None, parent_id=task.parent_id)
    _validate_parent_sprint(parent, task.sprint_id)
    db_item = models.WorkItem(
        **task.model_dump(exclude_unset=True), project_id=project_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    admin_service.log_activity(
        db,
        task_id=db_item.id,
        user_id=user_id,
        action="CREATE_TASK",
    )
    return db_item


def get_work_items(
    db: Session,
    project_id: int,
    status: str | None = None,
    assignee_id: int | None = None,
    sprint_id: int | None = None,
    task_type: str | None = None,
) -> list[models.WorkItem]:
    statement = select(models.WorkItem).where(models.WorkItem.project_id == project_id)
    if status is not None:
        normalized_status = _normalize_status_value(status)
        statement = statement.where(func.replace(func.lower(models.WorkItem.status), " ", "") == normalized_status)
    if assignee_id is not None:
        statement = statement.where(models.WorkItem.assignee_id == assignee_id)
    if sprint_id is not None:
        statement = statement.where(models.WorkItem.sprint_id == sprint_id)
    if task_type is not None:
        statement = statement.where(models.WorkItem.type == task_type)
    statement = statement.order_by(models.WorkItem.id.asc())
    return list(db.scalars(statement).all())


def get_work_item(
    db: Session,
    task_id: int,
) -> models.WorkItem | None:
    statement = select(models.WorkItem).where(models.WorkItem.id == task_id)
    return db.execute(statement).scalar_one_or_none()


def update_work_item(
    db: Session,
    task_id: int,
    update_data: schemas.WorkItemUpdate,
    user_id: int,
) -> models.WorkItem | None:
    db_item = get_work_item(db, task_id)
    if not db_item:
        return None
    updates = cast(dict[str, object], update_data.model_dump(exclude_unset=True))
    task_type = updates.get("type")
    if isinstance(task_type, str):
        _validate_task_type(db, task_type)
    next_parent_id = cast(int | None, updates["parent_id"]) if "parent_id" in updates else db_item.parent_id
    next_sprint_id = cast(int | None, updates["sprint_id"]) if "sprint_id" in updates else db_item.sprint_id
    parent = _validate_parent(
        db,
        project_id=db_item.project_id,
        task_id=task_id,
        parent_id=next_parent_id,
    )
    _validate_parent_sprint(parent, next_sprint_id)

    sprint_changed = "sprint_id" in updates and db_item.sprint_id != next_sprint_id
    for key, value in updates.items():
        old_value = getattr(db_item, key, None)
        if old_value == value:
            continue
        setattr(db_item, key, value)
        admin_service.log_activity(
            db,
            task_id=task_id,
            user_id=user_id,
            action="UPDATE_FIELD",
            field_name=key,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(value) if value is not None else None,
        )
    db.commit()
    db.refresh(db_item)
    if sprint_changed:
        _cascade_sprint_to_descendants(
            db,
            task_id=task_id,
            sprint_id=cast(int | None, db_item.sprint_id),
            user_id=user_id,
        )
    return db_item


def delete_work_item(
    db: Session,
    task_id: int,
    user_id: int,
) -> bool:
    return _delete_work_item_tree(db, task_id=task_id, user_id=user_id)


def update_work_item_status(
    db: Session,
    task_id: int,
    new_status: str,
    user_id: int,
) -> models.WorkItem | None:
    db_item = get_work_item(db, task_id)
    if not db_item:
        return None

    old_status = db_item.status
    if old_status == new_status:
        return db_item

    db_item.status = new_status

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    # Rejestrowanie logu audytowego - UC7
    admin_service.log_activity(
        db,
        task_id=task_id,
        user_id=user_id,
        action="STATUS_CHANGE",
        field_name="status",
        old_value=old_status,
        new_value=new_status,
    )
    return db_item


def create_time_log(
    db: Session,
    task_id: int,
    log_data: schemas.TimeLogCreate,
    user_id: int,
) -> models.TimeLog | None:
    if not get_work_item(db, task_id):
        return None

    db_log = models.TimeLog(**log_data.model_dump(), work_item_id=task_id, user_id=user_id)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    admin_service.log_activity(
        db,
        task_id=task_id,
        user_id=user_id,
        action="LOG_WORK",
    )
    return db_log


def get_time_logs(db: Session, task_id: int) -> list[models.TimeLog] | None:
    if not get_work_item(db, task_id):
        return None

    statement = (
        select(models.TimeLog)
        .where(models.TimeLog.work_item_id == task_id)
        .order_by(models.TimeLog.created_at.asc(), models.TimeLog.id.asc())
    )
    return list(db.scalars(statement).all())
