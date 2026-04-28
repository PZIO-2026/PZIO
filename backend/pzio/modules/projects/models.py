import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pzio.db import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    creation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), default="Aktywny")

    # Relacje
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Planned")

    project = relationship("Project", back_populates="sprints")


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # SAD wspomina o tablicy ról np. ["Developer", "Tester"]. Używamy JSON dla kompatybilności SQLite z pliku db.py
    roles: Mapped[list[str]] = mapped_column(JSON, default=list) 

    project = relationship("Project", back_populates="members")