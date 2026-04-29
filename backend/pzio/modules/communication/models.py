from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pzio.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Comment(Base):
    """A text comment attached to a task (WorkItem)."""

    __tablename__ = "comments"

    comment_id: Mapped[int] = mapped_column("comment_id", Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column("task_id", Integer, nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(
        "author_id",
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column("content", Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class Attachment(Base):
    """A file attachment linked to a task (WorkItem)."""

    __tablename__ = "attachments"

    attachment_id: Mapped[int] = mapped_column("attachment_id", Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column("task_id", Integer, nullable=False, index=True)
    uploader_id: Mapped[int] = mapped_column(
        "uploader_id",
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column("filename", String(255), nullable=False)
    content_type: Mapped[str] = mapped_column("content_type", String(128), nullable=False, default="application/octet-stream")
    file_path: Mapped[str] = mapped_column("file_path", String(512), nullable=False)
    file_size: Mapped[int] = mapped_column("file_size", Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
