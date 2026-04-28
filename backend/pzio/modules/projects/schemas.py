"""
Pydantic v2 schemas for the `projects` module.
Location: backend/pzio/modules/projects/schemas.py

Naming convention:
  - *Create  – request body for POST
  - *Update  – request body for PATCH (all fields Optional)
  - *Out     – response body
  - *Page    – paginated response wrapper
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .models import ProjectStatus, SprintStatus


# ---------------------------------------------------------------------------
# Generic paginated response
# ---------------------------------------------------------------------------

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Universal paginated response – maps to {items, total, page, size}."""

    items: list[T]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Project schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    """POST /api/projects – request body."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)


class ProjectUpdate(BaseModel):
    """PATCH /api/projects/{id} – all fields optional (partial update)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)


class ProjectStats(BaseModel):
    """Embedded statistics returned on GET /api/projects/{id}."""

    member_count: int
    sprint_count: int

    model_config = ConfigDict(from_attributes=True)


class ProjectOut(BaseModel):
    """Standard project response body."""

    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailOut(ProjectOut):
    """Extended project response body (single project endpoint) with stats."""

    stats: ProjectStats


# ---------------------------------------------------------------------------
# ProjectMember schemas
# ---------------------------------------------------------------------------

class ProjectMemberCreate(BaseModel):
    """POST /api/projects/{id}/members – request body."""

    userId: str = Field(..., alias="userId")
    roles: list[str] = Field(..., min_length=1)

    model_config = ConfigDict(populate_by_name=True)


class ProjectMemberOut(BaseModel):
    """Response body for a single project member."""

    id: str
    project_id: str
    user_id: str
    roles: list[str]
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Sprint schemas
# ---------------------------------------------------------------------------

class SprintCreate(BaseModel):
    """POST /api/projects/{id}/sprints – request body."""

    name: str = Field(..., min_length=1, max_length=255)
    startDate: datetime = Field(..., alias="startDate")
    endDate: datetime = Field(..., alias="endDate")

    model_config = ConfigDict(populate_by_name=True)


class SprintUpdate(BaseModel):
    """PATCH /api/sprints/{id} – all fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    startDate: Optional[datetime] = Field(default=None, alias="startDate")
    endDate: Optional[datetime] = Field(default=None, alias="endDate")
    status: Optional[SprintStatus] = None

    model_config = ConfigDict(populate_by_name=True)


class SprintOut(BaseModel):
    """Response body for a sprint."""

    id: str
    project_id: str
    name: str
    status: SprintStatus
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Burndown chart schemas
# ---------------------------------------------------------------------------

class BurndownDay(BaseModel):
    """Single data point on the burndown chart."""

    date: datetime
    remainingPoints: int = Field(..., alias="remainingPoints")

    model_config = ConfigDict(populate_by_name=True)


class BurndownOut(BaseModel):
    """Response body for GET /api/sprints/{id}/burndown."""

    sprintId: str = Field(..., alias="sprintId")
    totalPoints: int = Field(..., alias="totalPoints")
    days: list[BurndownDay]

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


# ---------------------------------------------------------------------------
# Query-param schemas (used as FastAPI Depends)
# ---------------------------------------------------------------------------

class ProjectListParams(BaseModel):
    """Query parameters for GET /api/projects."""

    status: Optional[ProjectStatus] = None
    search: Optional[str] = None
    sortBy: Optional[str] = Field(default="created_at")
    sortDirection: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class MemberListParams(BaseModel):
    """Query parameters for GET /api/projects/{id}/members."""

    role: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
