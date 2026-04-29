from typing import cast

from sqlalchemy.orm import Session

from . import models, schemas


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
    query = db.query(models.WorkItem).filter(models.WorkItem.project_id == project_id)
    if status is not None:
        query = query.filter(models.WorkItem.status == status)
    if assignee_id is not None:
        query = query.filter(models.WorkItem.assignee_id == assignee_id)
    if sprint_id is not None:
        query = query.filter(models.WorkItem.sprint_id == sprint_id)
    if task_type is not None:
        query = query.filter(models.WorkItem.type == task_type)
    return query.all()


def get_work_item(
    db: Session,
    task_id: int,
) -> models.WorkItem | None:
    return db.query(models.WorkItem).filter(models.WorkItem.id == task_id).first()


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
    activity_log = models.ActivityLog(
        work_item_id=task_id,
        user_id=user_id,
        action="STATUS_CHANGE",
        old_status=old_status,
        new_status=new_status,
    )
    db.add(activity_log)
    db.commit()
    db.refresh(db_item)
    return db_item


def create_time_log(
    db: Session,
    task_id: int,
    log_data: schemas.TimeLogCreate,
    user_id: int,
) -> models.TimeLog:
    db_log = models.TimeLog(
        **log_data.model_dump(), work_item_id=task_id, user_id=user_id
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_time_logs(db: Session, task_id: int) -> list[models.TimeLog]:
    return db.query(models.TimeLog).filter(models.TimeLog.work_item_id == task_id).all()
