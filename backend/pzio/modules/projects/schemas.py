from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

# --- PROJECT SCHEMAS ---

class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class ProjectSummary(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(ProjectSummary):
    creation_date: datetime = Field(alias="creationDate")
    # Statystyki opisane w SAD
    member_count: int = Field(0, alias="memberCount")
    task_count: int = Field(0, alias="taskCount")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class PaginatedProjects(BaseModel):
    items: List[ProjectSummary]
    total: int
    page: int
    size: int

# --- MEMBER SCHEMAS ---

class ProjectMemberAdd(BaseModel):
    user_id: UUID = Field(alias="userId")
    roles: List[str]
    model_config = ConfigDict(populate_by_name=True)

class ProjectMemberResponse(BaseModel):
    user_id: UUID = Field(alias="userId")
    roles: List[str]
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --- SPRINT SCHEMAS ---

class SprintCreate(BaseModel):
    name: str
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    model_config = ConfigDict(populate_by_name=True)

class SprintUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = Field(None, alias="startDate")
    end_date: Optional[date] = Field(None, alias="endDate")
    status: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

class SprintResponse(BaseModel):
    id: UUID
    name: str
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    status: str
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --- BURNDOWN SCHEMAS ---

class BurndownDay(BaseModel):
    date: date
    remaining_points: int = Field(alias="remainingPoints")
    model_config = ConfigDict(populate_by_name=True)

class BurndownResponse(BaseModel):
    sprint_id: UUID = Field(alias="sprintId")
    total_points: int = Field(alias="totalPoints")
    days: List[BurndownDay]
    model_config = ConfigDict(populate_by_name=True)