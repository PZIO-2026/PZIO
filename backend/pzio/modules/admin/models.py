from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from pzio.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskType(Base):
    """System dictionary entry — a single task type (SAD §3.5, FR22)."""

    __tablename__ = "task_types"

    task_type_id: Mapped[int] = mapped_column("task_type_id", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("name", String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )


class Backup(Base):
    """Metadata of a forced database backup (SAD §3.5, FR23)."""

    __tablename__ = "backups"

    backup_id: Mapped[int] = mapped_column("backup_id", Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column("file_path", String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column("status", String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )


class ActivityLog(Base):
    """Audit log entry — single recorded change of a task (SAD §3.5, FR24)."""

    __tablename__ = "activity_logs"

    activity_log_id: Mapped[int] = mapped_column(
        "activity_log_id", Integer, primary_key=True, autoincrement=True
    )
    task_id: Mapped[int] = mapped_column("task_id", Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column("action", String(50), nullable=False)
    field_name: Mapped[str | None] = mapped_column("field_name", String(50), nullable=True, default=None)
    old_value: Mapped[str | None] = mapped_column("old_value", String(500), nullable=True, default=None)
    new_value: Mapped[str | None] = mapped_column("new_value", String(500), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
