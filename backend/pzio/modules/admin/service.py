import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pzio.modules.admin.models import ActivityLog, Backup, TaskType
from pzio.modules.admin.schemas import TaskTypeCreate


class TaskTypeAlreadyExistsError(Exception):
    """Raised when adding a task type whose name already exists (→ 409)."""


class BackupFailedError(Exception):
    """Raised when the database file cannot be copied (→ 500)."""


def create_task_type(db: Session, payload: TaskTypeCreate) -> TaskType:
    """Add a new task type to the system dictionary (Admin only)."""
    name = payload.name.strip()
    existing = db.execute(select(TaskType).where(TaskType.name == name)).scalar_one_or_none()
    if existing is not None:
        raise TaskTypeAlreadyExistsError(name)

    task_type = TaskType(name=name)
    db.add(task_type)
    try:
        db.commit()
    except IntegrityError:
        # Race-condition fallback: a parallel request committed the same name first.
        db.rollback()
        raise TaskTypeAlreadyExistsError(name)
    db.refresh(task_type)
    return task_type


def list_task_types(db: Session) -> Sequence[TaskType]:
    """Return all task types ordered by id (insertion order)."""
    stmt = select(TaskType).order_by(TaskType.task_type_id.asc())
    return db.scalars(stmt).all()


_SQLITE_PREFIXES = ("sqlite:///", "sqlite+pysqlite:///")


def _resolve_sqlite_file(database_url: str) -> Path | None:
    """Extract the on-disk path from a SQLite URL.

    SQLAlchemy uses `sqlite:///<rel>` for relative and `sqlite:////<abs>` for
    absolute paths — `urlparse` mangles the leading slashes, so we strip the
    prefix manually. Returns None for non-SQLite URLs and for in-memory SQLite,
    both of which cannot be backed up via simple file copy.
    """
    for prefix in _SQLITE_PREFIXES:
        if database_url.startswith(prefix):
            raw = database_url[len(prefix):]
            if not raw or raw == ":memory:":
                return None
            return Path(raw)
    return None


def create_backup(db: Session, database_url: str, backup_dir: str) -> Backup:
    """Force a backup of the SQLite database file.

    Strategy: copy the live `.db` file into `backup_dir` with a UTC timestamp suffix.
    A `Backup` row is recorded in either case ("completed" / "failed") so admins can
    audit attempts. On failure, we still raise — the router maps that to HTTP 500.
    """
    source = _resolve_sqlite_file(database_url)
    timestamp = datetime.now(timezone.utc)

    if source is None or not source.exists():
        record = Backup(file_path="", status="failed", created_at=timestamp)
        db.add(record)
        db.commit()
        db.refresh(record)
        raise BackupFailedError(
            "Database file is not available for a file-level backup "
            "(only local SQLite is supported)."
        )

    target_dir = Path(backup_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"pzio_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.db"
    destination = target_dir / filename

    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        record = Backup(file_path=str(destination), status="failed", created_at=timestamp)
        db.add(record)
        db.commit()
        db.refresh(record)
        raise BackupFailedError(str(exc))

    record = Backup(file_path=str(destination), status="completed", created_at=timestamp)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_task_history(db: Session, task_id: int) -> Sequence[ActivityLog]:
    """Return all audit entries for a task in chronological order.

    The `tasks` module is still a skeleton (FR07–FR15), so we don't validate that
    the task exists — an unknown id simply returns an empty list. This keeps the
    endpoint usable while the audit infrastructure is wired up.
    """
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.task_id == task_id)
        .order_by(ActivityLog.created_at.asc(), ActivityLog.activity_log_id.asc())
    )
    return db.scalars(stmt).all()


def log_activity(
    db: Session,
    *,
    task_id: int,
    user_id: int,
    action: str,
    field_name: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> ActivityLog:
    """Helper used by other modules (e.g. tasks) to record a change.

    Kept intentionally thin so callers can wrap it in their own transactions.
    """
    entry = ActivityLog(
        task_id=task_id,
        user_id=user_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
