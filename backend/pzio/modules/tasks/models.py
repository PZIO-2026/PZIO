from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.sql import func

from ...db import Base
from pzio.modules.admin.models import ActivityLog


class WorkItem(Base):
    __tablename__: str = "work_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    story_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("work_items.id"), nullable=True
    )
    assignee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sprint_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="ToDo", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    time_logs: Mapped[list["TimeLog"]] = relationship(
        "TimeLog", back_populates="work_item", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[list[ActivityLog]] = relationship(
        ActivityLog,
        primaryjoin=lambda: WorkItem.id == foreign(ActivityLog.task_id),
        viewonly=True,
    )


class TimeLog(Base):
    __tablename__: str = "time_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("work_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    hours_spent: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    work_item: Mapped["WorkItem"] = relationship("WorkItem", back_populates="time_logs")
