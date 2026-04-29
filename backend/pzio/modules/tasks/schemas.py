from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class WorkItemBase(BaseModel):
    title: str
    description: str | None = None
    type: str
    priority: str
    story_points: int | None = Field(None, alias="storyPoints")
    parent_id: int | None = Field(None, alias="parentId")
    assignee_id: int | None = Field(None, alias="assigneeId")
    sprint_id: int | None = Field(None, alias="sprintId")

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)


class WorkItemCreate(WorkItemBase):
    pass


class WorkItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    type: str | None = None
    priority: str | None = None
    story_points: int | None = Field(None, alias="storyPoints")
    parent_id: int | None = Field(None, alias="parentId")
    assignee_id: int | None = Field(None, alias="assigneeId")
    sprint_id: int | None = Field(None, alias="sprintId")

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)


class StatusUpdate(BaseModel):
    status: str


class WorkItemResponse(WorkItemBase):
    id: int
    project_id: int = Field(alias="projectId")
    status: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True, populate_by_name=True
    )


class TimeLogCreate(BaseModel):
    hours_spent: float = Field(..., alias="hoursSpent")
    note: str | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)


class TimeLogResponse(TimeLogCreate):
    id: int
    work_item_id: int = Field(alias="workItemId")
    created_at: datetime = Field(alias="createdAt")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True, populate_by_name=True
    )
