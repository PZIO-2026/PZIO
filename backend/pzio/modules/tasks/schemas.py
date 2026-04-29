from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class WorkItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    priority: str
    story_points: Optional[int] = Field(None, alias="storyPoints")
    parent_id: Optional[int] = Field(None, alias="parentId")
    assignee_id: Optional[int] = Field(None, alias="assigneeId")
    sprint_id: Optional[int] = Field(None, alias="sprintId")

    model_config = ConfigDict(populate_by_name=True)

class WorkItemCreate(WorkItemBase):
    pass

class WorkItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    story_points: Optional[int] = Field(None, alias="storyPoints")
    parent_id: Optional[int] = Field(None, alias="parentId")
    assignee_id: Optional[int] = Field(None, alias="assigneeId")
    sprint_id: Optional[int] = Field(None, alias="sprintId")

    model_config = ConfigDict(populate_by_name=True)

class StatusUpdate(BaseModel):
    status: str

class WorkItemResponse(WorkItemBase):
    id: int
    project_id: int = Field(alias="projectId")
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TimeLogCreate(BaseModel):
    hours_spent: float = Field(..., alias="hoursSpent")
    note: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class TimeLogResponse(TimeLogCreate):
    id: int
    work_item_id: int = Field(alias="workItemId")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)