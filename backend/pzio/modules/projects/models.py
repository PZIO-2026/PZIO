"""
SQLAlchemy ORM models for the `projects` module.
Location: backend/pzio/modules/projects/models.py
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pzio.db import Base



# ENUMS
class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SprintStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


class ProjectRole(str, enum.Enum):
    DEVELOPER = "developer"
    QA = "qa"
    SCRUM_MASTER = "scrum_master"
    PROJECT_OWNER = "project_owner"
    MAINTAINER = "maintainer"


MEMBERSHIP_MANAGER_ROLES: frozenset[ProjectRole] = frozenset(
    {ProjectRole.PROJECT_OWNER, ProjectRole.SCRUM_MASTER, ProjectRole.MAINTAINER}
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# PROJECT
class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[int] = mapped_column(
        "project_id", Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False, length=20),
        nullable=False,
        default=ProjectStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    sprints: Mapped[list["Sprint"]] = relationship(
        "Sprint", back_populates="project", cascade="all, delete-orphan"
    )


# PROJECT MEMBER
class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(
        "id", Integer, primary_key=True, autoincrement=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    roles: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)).with_variant(JSON, "sqlite"), nullable=False, default=list
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    project: Mapped["Project"] = relationship("Project", back_populates="members")


# SPRINT
class Sprint(Base):
    __tablename__ = "sprints"

    sprint_id: Mapped[int] = mapped_column(
        "sprint_id", Integer, primary_key=True, autoincrement=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SprintStatus] = mapped_column(
        Enum(SprintStatus, native_enum=False, length=20),
        nullable=False,
        default=SprintStatus.PLANNED,
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    project: Mapped["Project"] = relationship("Project", back_populates="sprints")