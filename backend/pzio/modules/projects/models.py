"""
SQLAlchemy ORM models for the `projects` module.
Location: backend/pzio/modules/projects/models.py
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    ARRAY,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Assumes a shared Base is declared in e.g. backend/pzio/database.py
from pzio.db import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SprintStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"
    __allow_unmapped__ = True 

    id: str = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    name: str = Column(String(255), nullable=False)
    description: str | None = Column(Text, nullable=True)
    status: str = Column(
        Enum(ProjectStatus, name="project_status"),
        nullable=False,
        default=ProjectStatus.ACTIVE,
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    members: list["ProjectMember"] = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    sprints: list["Sprint"] = relationship(
        "Sprint", back_populates="project", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# ProjectMember
# ---------------------------------------------------------------------------

class ProjectMember(Base):
    __tablename__ = "project_members"
    __allow_unmapped__ = True

    """
    Join table between Project and a user (referenced only by userId string).
    `roles` is stored as a PostgreSQL ARRAY of text values.
    """

    id: str = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    project_id: str = Column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: str = Column(String(255), nullable=False, index=True)
    roles: list[str] = Column(
        ARRAY(String).with_variant(JSON, "sqlite"), 
        nullable=False, 
        default=list
    )
    joined_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project: "Project" = relationship("Project", back_populates="members")


# ---------------------------------------------------------------------------
# Sprint
# ---------------------------------------------------------------------------

class Sprint(Base):
    __tablename__ = "sprints"
    __allow_unmapped__ = True 

    id: str = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    project_id: str = Column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: str = Column(String(255), nullable=False)
    status: str = Column(
        Enum(SprintStatus, name="sprint_status"),
        nullable=False,
        default=SprintStatus.PLANNED,
    )
    start_date: datetime = Column(DateTime(timezone=True), nullable=False)
    end_date: datetime = Column(DateTime(timezone=True), nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project: "Project" = relationship("Project", back_populates="sprints")
