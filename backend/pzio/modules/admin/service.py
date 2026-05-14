import shutil
import subprocess
import zipfile
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from testcontainers.core.container import DockerContainer

from pzio.modules.admin.models import ActivityLog, Backup, TaskType
from pzio.modules.admin.schemas import TaskTypeCreate


class TaskTypeAlreadyExistsError(Exception):
    """Raised when adding a task type whose name already exists (→ 409)."""


class BackupFailedError(Exception):
    """Raised when the database file cannot be copied (→ 500)."""


class BackupInProgressError(Exception):
    """Raised when a backup is already running (→ 409)."""


class BackupAlreadyExistsError(Exception):
    """Raised when a backup with same name already exists (→ 409)."""


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
    except IntegrityError:  # pragma: no cover -- should be prevented by the pre-check
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
            raw = database_url[len(prefix) :]
            if not raw or raw == ":memory:":
                return None
            return Path(raw)
    return None


def _backup_sqlite_db(database_url: str, target_dir: Path, base_filename: str) -> str:
    source = _resolve_sqlite_file(database_url)
    if source is None or not source.exists():
        raise BackupFailedError(
            "Database file is not available for a file-level backup "
            "(only local SQLite and PostgreSQL string connections are supported)."
        )

    destination = target_dir / f"{base_filename}.db"
    shutil.copy2(source, destination)
    return str(destination)


def _pg_zip_sql(sql_dest: Path, zip_dest: Path) -> str:
    """Helper to zip the generated .sql file and remove the original."""
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(sql_dest, arcname=sql_dest.name)
    sql_dest.unlink(missing_ok=True)
    return str(zip_dest)


def _run_pg_dump_local(clean_url: str, sql_dest: Path) -> None:
    subprocess.run(["pg_dump", clean_url, "-f", str(sql_dest)], check=True, capture_output=True)


def _run_pg_dump_testcontainers(clean_url: str, target_dir: Path, sql_dest: Path) -> None:
    container = DockerContainer(
        image="postgres:16-alpine",
        volumes=[(str(target_dir.absolute()), "/backup", "rw")],
        command=f"pg_dump {clean_url} -f /backup/{sql_dest.name}",
        network_mode="host",
    )
    with container:
        # The container will run the pg_dump command and exit.
        # Wait for the process to finish directly.
        c = container.get_wrapped_container()
        result = c.wait()

        if result.get("StatusCode", 1) != 0:
            raise RuntimeError(f"pg_dump via testcontainers failed with status {result.get('StatusCode')}")
        if not sql_dest.exists():
            raise RuntimeError("pg_dump via testcontainers did not produce the expected file")


def _zip_postgres_data_dir(db: Session, target_dir: Path, base_filename: str) -> str:
    try:
        data_dir = db.execute(text("SHOW data_directory;")).scalar()
        if data_dir and Path(data_dir).exists():
            zip_dest = target_dir / f"{base_filename}_data_dir.zip"
            shutil.make_archive(str(zip_dest.with_suffix("")), "zip", data_dir)
            return str(zip_dest)
        else:
            raise BackupFailedError(
                "All PostgreSQL backup methods failed (pg_dump, docker pg_dump, data_directory zip)."
            )
    except Exception as e:
        raise BackupFailedError(f"PostgreSQL backup failed: {e}")


def _backup_postgres_db(db: Session, database_url: str, target_dir: Path, base_filename: str) -> str:
    clean_url = re.sub(r"postgresql\+[^:]+://", "postgresql://", database_url)
    sql_dest = target_dir / f"{base_filename}.sql"
    zip_dest = target_dir / f"{base_filename}.zip"

    # 1. Attempt pg_dump locally
    try:
        _run_pg_dump_local(clean_url, sql_dest)
        return _pg_zip_sql(sql_dest, zip_dest)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 2. Attempt testcontainers pg_dump (Docker)
    try:
        _run_pg_dump_testcontainers(clean_url, target_dir, sql_dest)
        return _pg_zip_sql(sql_dest, zip_dest)
    except Exception:
        pass

    # 3. Zip data directory if all dumps fail completely
    return _zip_postgres_data_dir(db, target_dir, base_filename)


def create_backup(db: Session, database_url: str, backup_dir: str) -> Backup:
    """Force a backup of the SQLite or PostgreSQL database.

    Strategy:
    - SQLite: copy the live `.db` file into `backup_dir` with a UTC timestamp suffix.
    - PostgreSQL: attempt pg_dump, fallback to testcontainers pg_dump, fallback to zipping data_directory.
    A `Backup` row is recorded in either case ("completed" / "failed") so admins can
    audit attempts. On failure, we still raise - the router maps that to HTTP 500.
    """
    in_progress = db.execute(select(Backup).where(Backup.status == "in_progress")).first()
    if in_progress is not None:
        raise BackupInProgressError("A backup is already in progress.")

    timestamp = datetime.now(timezone.utc)
    target_dir = Path(backup_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    base_filename = f"pzio_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"

    existing_db = db.execute(select(Backup).where(Backup.file_path.like(f"%{base_filename}%"))).first()
    if existing_db is not None:
        raise BackupAlreadyExistsError(f"Backup with name {base_filename} already exists.")

    record = Backup(file_path="", status="in_progress", created_at=timestamp)
    db.add(record)
    db.commit()
    db.refresh(record)

    is_postgres = database_url.startswith(("postgresql://", "postgresql+", "postgres://"))

    destination = ""
    success = False
    error_msg = ""

    try:
        if is_postgres:
            destination = _backup_postgres_db(db, database_url, target_dir, base_filename)
        else:
            destination = _backup_sqlite_db(database_url, target_dir, base_filename)
        success = True
    except Exception as exc:
        success = False
        error_msg = str(exc)

    record.file_path = destination
    record.status = "completed" if success else "failed"
    db.add(record)
    db.commit()
    db.refresh(record)

    if not success:
        raise BackupFailedError(error_msg)

    return record


def get_task_history(db: Session, task_id: int) -> Sequence[ActivityLog]:
    """Return all audit entries for a task in chronological order.

    The `tasks` module is still a skeleton (FR07-FR15), so we don't validate that
    the task exists - an unknown id simply returns an empty list. This keeps the
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
