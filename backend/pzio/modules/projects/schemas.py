"""
Naming convention:
  - Create  - request body for POST
  - Update  - request body for PATCH (all fields Optional)
  - Out     - response body (camelCase serialisation aliases, snake_case internals)
  - Page    - generic paginated response wrapper

Aligned with the auth module conventions:
  - Integer primary keys
  - serialization_alias for camelCase JSON output
  - populate_by_name=True so services can use Python attribute names directly
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .models import ProjectRole, ProjectStatus, SprintStatus



# PAGINATION RESPONSE
T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Universal paginated response - maps to {items, total, page, size}."""

    items: list[T]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)


# PROJECT SCHEMAS
class ProjectCreate(BaseModel):
    """POST /api/projects - request body."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Apollo Migration",
                "description": "Migrate the legacy Apollo billing engine to the new microservice platform.",
            }
        }
    )


class ProjectUpdate(BaseModel):
    """PATCH /api/projects/{id} - all fields optional (partial update)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[ProjectStatus] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Apollo Migration (Phase 2)",
                "status": "active",
            }
        }
    )


class ProjectStats(BaseModel):
    """Embedded statistics returned on GET /api/projects/{id}."""

    member_count: int = Field(serialization_alias="memberCount")
    sprint_count: int = Field(serialization_alias="sprintCount")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={"example": {"memberCount": 6, "sprintCount": 3}},
    )



class ProjectOut(BaseModel):
    """Standard project response body."""

    project_id: int = Field(serialization_alias="projectId")
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    current_user_roles: list[ProjectRole] = Field(
        default_factory=list,
        serialization_alias="currentUserRoles",
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "projectId": 7,
                "name": "Apollo Migration",
                "description": "Migrate the legacy Apollo billing engine to the new microservice platform.",
                "status": "active",
                "currentUserRoles": ["project_owner"],
                "createdAt": "2026-05-14T09:30:00Z",
                "updatedAt": "2026-05-14T09:30:00Z",
            }
        },
    )


class ProjectDetailOut(ProjectOut):
    """Extended project response (single GET) with stats."""
    stats: ProjectStats

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "projectId": 7,
                "name": "Apollo Migration",
                "description": "Migrate the legacy Apollo billing engine to the new microservice platform.",
                "status": "active",
                "currentUserRoles": ["project_owner"],
                "createdAt": "2026-05-14T09:30:00Z",
                "updatedAt": "2026-05-14T09:30:00Z",
                "stats": {"memberCount": 6, "sprintCount": 3},
            }
        },
    )

# PROJECT MEMBER SCHEMAS
class ProjectMemberCreate(BaseModel):
    """POST /api/projects/{id}/members – request body."""

    email: str = Field(..., max_length=255, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    roles: list[ProjectRole] = Field(..., min_length=1)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "bob@example.com",
                "roles": ["developer", "qa_engineer"],
            }
        },
    )

class ProjectMemberUpdate(BaseModel):
    """PATCH /api/projects/{id}/members/ – request body for role update."""

    roles: list[ProjectRole] = Field(..., min_length=1)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"roles": ["scrum_master"]}},
    )


class ProjectMemberOut(BaseModel):
    """Response body for a single project member."""

    id: int
    project_id: int = Field(serialization_alias="projectId")
    user_id: int = Field(serialization_alias="userId")
    roles: list[ProjectRole]
    joined_at: datetime = Field(serialization_alias="joinedAt")
    first_name: Optional[str] = Field(default=None, serialization_alias="firstName")
    last_name: Optional[str] = Field(default=None, serialization_alias="lastName")
    email: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 15,
                "projectId": 7,
                "userId": 88,
                "roles": ["developer"],
                "joinedAt": "2026-05-14T10:00:00Z",
                "firstName": "Bob",
                "lastName": "Brown",
                "email": "bob@example.com",
            }
        },
    )


# SPRINT SCHEMAS
class SprintCreate(BaseModel):
    """POST /api/projects/{id}/sprints - request body."""

    name: str = Field(..., min_length=1, max_length=255)
    start_date: datetime = Field(..., alias="startDate")
    end_date: datetime = Field(..., alias="endDate")
    goal: Optional[str] = Field(default=None, max_length=1500)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Sprint 1",
                "startDate": "2026-05-15T00:00:00Z",
                "endDate": "2026-05-29T00:00:00Z",
                "goal": "Ship the auth flow and basic backlog UI.",
            }
        },
    )


class SprintUpdate(BaseModel):
    """PATCH /api/sprints/{id} - all fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    start_date: Optional[datetime] = Field(default=None, alias="startDate")
    end_date: Optional[datetime] = Field(default=None, alias="endDate")
    status: Optional[SprintStatus] = None
    goal: Optional[str] = Field(default=None, max_length=1500)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {"status": "active", "goal": "Updated goal mid-sprint."}
        },
    )


class SprintOut(BaseModel):
    """Response body for a sprint."""

    sprint_id: int = Field(serialization_alias="sprintId")
    project_id: int = Field(serialization_alias="projectId")
    name: str
    status: SprintStatus
    goal: Optional[str] = Field(default=None, max_length=1500)
    start_date: datetime = Field(serialization_alias="startDate")
    end_date: datetime = Field(serialization_alias="endDate")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "sprintId": 21,
                "projectId": 7,
                "name": "Sprint 1",
                "status": "planned",
                "goal": "Ship the auth flow and basic backlog UI.",
                "startDate": "2026-05-15T00:00:00Z",
                "endDate": "2026-05-29T00:00:00Z",
                "createdAt": "2026-05-14T11:00:00Z",
                "updatedAt": "2026-05-14T11:00:00Z",
            }
        },
    )


# BURNDOWN CHART SCHEMAS
class BurndownDay(BaseModel):
    """Single data point on the burndown chart."""

    date: datetime
    remainingPoints: int = Field(..., serialization_alias="remainingPoints")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {"date": "2026-05-15T00:00:00Z", "remainingPoints": 34}
        },
    )


class BurndownOut(BaseModel):
    """Response body for GET /api/sprints/{id}/burndown."""

    sprint_id: int = Field(..., serialization_alias="sprintId")
    total_points: int = Field(..., serialization_alias="totalPoints")
    days: list[BurndownDay]

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sprintId": 21,
                "totalPoints": 34,
                "days": [
                    {"date": "2026-05-15T00:00:00Z", "remainingPoints": 34},
                    {"date": "2026-05-16T00:00:00Z", "remainingPoints": 31},
                    {"date": "2026-05-17T00:00:00Z", "remainingPoints": 27},
                ],
            }
        },
    )



# QUERY PARAMETER SCHEMAS
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

    role: Optional[ProjectRole] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
