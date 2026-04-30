from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pzio.modules.admin import service as admin_service
from pzio.modules.tasks import models, schemas


def _normalize_status_value(value: str) -> str:
    return "".join(value.lower().split())


def create_work_item(
    db: Session,
    project_id: int,
    task: schemas.WorkItemCreate,
) -> models.WorkItem:
    db_item = models.WorkItem(
        **task.model_dump(exclude_unset=True), project_id=project_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
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
        statement = statement.where(
            func.replace(func.lower(models.WorkItem.status), " ", "")
            == normalized_status
        )
    if assignee_id is not None:
        statement = statement.where(models.WorkItem.assignee_id == assignee_id)
    if sprint_id is not None:
        statement = statement.where(models.WorkItem.sprint_id == sprint_id)
    if task_type is not None:
        statement = statement.where(models.WorkItem.type == task_type)
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
) -> models.WorkItem | None:
    db_item = get_work_item(db, task_id)
    if not db_item:
        return None
    updates = cast(dict[str, object], update_data.model_dump(exclude_unset=True))
    for key, value in updates.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_work_item(
    db: Session,
    task_id: int,
) -> bool:
    db_item = get_work_item(db, task_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True


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
    db_item.status = new_status

    # Rejestrowanie logu audytowego - UC7
    db.add(db_item)
    db.commit()
    admin_service.log_activity(
        db,
        task_id=task_id,
        user_id=user_id,
        action="STATUS_CHANGE",
        field_name="status",
        old_value=old_status,
        new_value=new_status,
    )
    db.refresh(db_item)
    return db_item


def create_time_log(
    db: Session,
    task_id: int,
    log_data: schemas.TimeLogCreate,
    user_id: int,
) -> models.TimeLog | None:
    if not get_work_item(db, task_id):
        return None

    db_log = models.TimeLog(
        **log_data.model_dump(), work_item_id=task_id, user_id=user_id
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_time_logs(db: Session, task_id: int) -> list[models.TimeLog] | None:
    if not get_work_item(db, task_id):
        return None

    statement = select(models.TimeLog).where(models.TimeLog.work_item_id == task_id)
    return list(db.scalars(statement).all())
